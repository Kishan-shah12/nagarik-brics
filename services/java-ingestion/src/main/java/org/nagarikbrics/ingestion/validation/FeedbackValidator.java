package org.nagarikbrics.ingestion.validation;

import org.nagarikbrics.ingestion.model.ApiError;
import org.nagarikbrics.ingestion.model.CitizenFeedbackRequest;
import org.nagarikbrics.ingestion.model.LocationCoords;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Aggressive input validator for citizen feedback submissions.
 *
 * <p>Validates every field of {@link CitizenFeedbackRequest} against the
 * strict constraints defined in the API contract (api-docs.md) and
 * JSON schema (SCHEMA.md). Validation is fail-fast for null/missing
 * required fields, but collects all errors for malformed values to give
 * the client maximum diagnostic information in a single response.</p>
 *
 * <h2>Validation Rules</h2>
 * <table>
 *   <tr><th>Field</th><th>Rule</th></tr>
 *   <tr><td>raw_text</td><td>Non-null, 10–5000 characters, no blank strings</td></tr>
 *   <tr><td>language</td><td>Non-null, must be in supported ISO 639-1 set</td></tr>
 *   <tr><td>location_coords</td><td>Non-null, lat [-90,90], lng [-180,180]</td></tr>
 *   <tr><td>country_code</td><td>Optional, must be valid BRICS code if present</td></tr>
 *   <tr><td>source_channel</td><td>Optional, must be in allowed set if present</td></tr>
 * </table>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
@Component
public class FeedbackValidator {

    /** Minimum allowed length for raw feedback text. */
    private final int minTextLength;

    /** Maximum allowed length for raw feedback text. */
    private final int maxTextLength;

    /** Set of supported ISO 639-1 language codes. */
    private final Set<String> supportedLanguages;

    /** Set of supported ISO 3166-1 alpha-2 country codes (BRICS nations). */
    private final Set<String> supportedCountries;

    /** Valid source channel identifiers. */
    private static final Set<String> VALID_CHANNELS = Set.of(
            "api", "web_form", "sms", "whatsapp", "partner_import"
    );

    /** Minimum valid latitude (South Pole). */
    private static final double MIN_LATITUDE = -90.0;

    /** Maximum valid latitude (North Pole). */
    private static final double MAX_LATITUDE = 90.0;

    /** Minimum valid longitude (International Date Line West). */
    private static final double MIN_LONGITUDE = -180.0;

    /** Maximum valid longitude (International Date Line East). */
    private static final double MAX_LONGITUDE = 180.0;

    /**
     * Constructs the validator with configuration from application.yml.
     *
     * @param minTextLength      minimum text length from config
     * @param maxTextLength      maximum text length from config
     * @param supportedLanguages comma-separated language codes from config
     * @param supportedCountries comma-separated country codes from config
     */
    public FeedbackValidator(
            @Value("${app.validation.min-text-length:10}") final int minTextLength,
            @Value("${app.validation.max-text-length:5000}") final int maxTextLength,
            @Value("${app.validation.supported-languages:hi,pt,en,ru,zh}") final String supportedLanguages,
            @Value("${app.validation.supported-countries:BR,RU,IN,CN,ZA}") final String supportedCountries) {
        this.minTextLength = minTextLength;
        this.maxTextLength = maxTextLength;
        this.supportedLanguages = Arrays.stream(supportedLanguages.split(","))
                .map(String::trim)
                .collect(Collectors.toUnmodifiableSet());
        this.supportedCountries = Arrays.stream(supportedCountries.split(","))
                .map(String::trim)
                .collect(Collectors.toUnmodifiableSet());
    }

    /**
     * Validates the entire feedback request.
     *
     * <p>Collects all validation errors into a list rather than failing
     * on the first error, so the client can fix all issues in one attempt.</p>
     *
     * @param request the feedback request to validate
     * @return list of field-level errors; empty list means validation passed
     */
    public List<ApiError.FieldError> validate(final CitizenFeedbackRequest request) {
        final List<ApiError.FieldError> errors = new ArrayList<>();

        if (request == null) {
            errors.add(new ApiError.FieldError("body", "Request body is required."));
            return errors;
        }

        validateRawText(request.getRawText(), errors);
        validateLanguage(request.getLanguage(), errors);
        validateLocationCoords(request.getLocationCoords(), errors);
        validateCountryCode(request.getCountryCode(), errors);
        validateSourceChannel(request.getSourceChannel(), errors);

        return errors;
    }

    /**
     * Validates the raw_text field.
     *
     * <p>Checks for null, blank, below minimum length, and above maximum
     * length. Uses {@link String#codePointCount(int, int)} to correctly
     * count characters in multilingual text (Hindi, Chinese, etc. may use
     * multi-byte code points).</p>
     *
     * @param rawText the raw text value to validate
     * @param errors  list to append errors to
     */
    private void validateRawText(final String rawText,
                                  final List<ApiError.FieldError> errors) {
        if (rawText == null) {
            errors.add(new ApiError.FieldError("raw_text",
                    "Field is required."));
            return;
        }

        if (rawText.isBlank()) {
            errors.add(new ApiError.FieldError("raw_text",
                    "Must not be blank."));
            return;
        }

        // Use codePointCount for correct multilingual character counting
        final int charCount = rawText.codePointCount(0, rawText.length());

        if (charCount < minTextLength) {
            errors.add(new ApiError.FieldError("raw_text",
                    String.format("Must be at least %d characters. Received %d.",
                            minTextLength, charCount)));
        }

        if (charCount > maxTextLength) {
            errors.add(new ApiError.FieldError("raw_text",
                    String.format("Must not exceed %d characters. Received %d.",
                            maxTextLength, charCount)));
        }
    }

    /**
     * Validates the language field against the supported ISO 639-1 code set.
     *
     * @param language the language code to validate
     * @param errors   list to append errors to
     */
    private void validateLanguage(final String language,
                                   final List<ApiError.FieldError> errors) {
        if (language == null) {
            errors.add(new ApiError.FieldError("language",
                    "Field is required. Provide an ISO 639-1 language code."));
            return;
        }

        if (!supportedLanguages.contains(language.toLowerCase())) {
            errors.add(new ApiError.FieldError("language",
                    String.format("Unsupported language code '%s'. Supported: %s.",
                            language, supportedLanguages)));
        }
    }

    /**
     * Validates GPS coordinates for presence, type correctness, and range.
     *
     * <p>Latitude must be within [-90.0, 90.0] and longitude within
     * [-180.0, 180.0]. Both components are required. Exact boundary
     * values (poles, date line) are valid.</p>
     *
     * @param coords the location coordinates to validate
     * @param errors list to append errors to
     */
    private void validateLocationCoords(final LocationCoords coords,
                                         final List<ApiError.FieldError> errors) {
        if (coords == null) {
            errors.add(new ApiError.FieldError("location_coords",
                    "Field is required. Provide lat and lng in decimal degrees."));
            return;
        }

        if (coords.getLat() == null) {
            errors.add(new ApiError.FieldError("location_coords.lat",
                    "Latitude is required."));
        } else if (Double.isNaN(coords.getLat()) || Double.isInfinite(coords.getLat())) {
            errors.add(new ApiError.FieldError("location_coords.lat",
                    "Latitude must be a finite number."));
        } else if (coords.getLat() < MIN_LATITUDE || coords.getLat() > MAX_LATITUDE) {
            errors.add(new ApiError.FieldError("location_coords.lat",
                    String.format("Must be between %.1f and %.1f. Received %.6f.",
                            MIN_LATITUDE, MAX_LATITUDE, coords.getLat())));
        }

        if (coords.getLng() == null) {
            errors.add(new ApiError.FieldError("location_coords.lng",
                    "Longitude is required."));
        } else if (Double.isNaN(coords.getLng()) || Double.isInfinite(coords.getLng())) {
            errors.add(new ApiError.FieldError("location_coords.lng",
                    "Longitude must be a finite number."));
        } else if (coords.getLng() < MIN_LONGITUDE || coords.getLng() > MAX_LONGITUDE) {
            errors.add(new ApiError.FieldError("location_coords.lng",
                    String.format("Must be between %.1f and %.1f. Received %.6f.",
                            MIN_LONGITUDE, MAX_LONGITUDE, coords.getLng())));
        }
    }

    /**
     * Validates the optional country_code field.
     *
     * <p>If provided, must be one of the five BRICS nation codes:
     * BR (Brazil), RU (Russia), IN (India), CN (China), ZA (South Africa).</p>
     *
     * @param countryCode the country code to validate (may be null)
     * @param errors      list to append errors to
     */
    private void validateCountryCode(final String countryCode,
                                      final List<ApiError.FieldError> errors) {
        if (countryCode != null && !supportedCountries.contains(countryCode.toUpperCase())) {
            errors.add(new ApiError.FieldError("country_code",
                    String.format("Invalid country code '%s'. Supported: %s.",
                            countryCode, supportedCountries)));
        }
    }

    /**
     * Validates the optional source_channel field.
     *
     * <p>If provided, must be one of: api, web_form, sms, whatsapp, partner_import.</p>
     *
     * @param sourceChannel the channel identifier to validate (may be null)
     * @param errors        list to append errors to
     */
    private void validateSourceChannel(final String sourceChannel,
                                        final List<ApiError.FieldError> errors) {
        if (sourceChannel != null && !VALID_CHANNELS.contains(sourceChannel.toLowerCase())) {
            errors.add(new ApiError.FieldError("source_channel",
                    String.format("Invalid source channel '%s'. Valid: %s.",
                            sourceChannel, VALID_CHANNELS)));
        }
    }
}

package org.nagarikbrics.ingestion.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Incoming citizen feedback request payload.
 *
 * <p>This is the data transfer object (DTO) for the
 * {@code POST /api/v1/feedback/submit} endpoint. It represents raw,
 * unprocessed citizen feedback as submitted by a citizen, NGO, or
 * data partner.</p>
 *
 * <h2>Required Fields</h2>
 * <ul>
 *   <li>{@code raw_text} — The citizen's feedback in their native language (10–5000 chars)</li>
 *   <li>{@code language} — ISO 639-1 language code (e.g., "hi", "pt", "en")</li>
 *   <li>{@code location_coords} — GPS coordinates of the infrastructure issue</li>
 * </ul>
 *
 * <h2>Optional Fields</h2>
 * <ul>
 *   <li>{@code country_code} — ISO 3166-1 alpha-2 (auto-inferred if omitted)</li>
 *   <li>{@code source_channel} — Submission channel (default: "api")</li>
 *   <li>{@code submitter_id} — Anonymous identifier (no PII)</li>
 * </ul>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 * @see CitizenFeedbackRecord
 * @see org.nagarikbrics.ingestion.validation.FeedbackValidator
 */
public class CitizenFeedbackRequest {

    /**
     * The citizen's raw feedback text in their native language.
     * Must be between 10 and 5000 characters inclusive.
     */
    @JsonProperty("raw_text")
    private String rawText;

    /**
     * ISO 639-1 language code of the feedback text.
     * Supported values: hi, pt, en, ru, zh, zu, af, ta, bn, mr, te, ur, kn, gu, ml.
     */
    @JsonProperty("language")
    private String language;

    /**
     * GPS coordinates (WGS 84) of the infrastructure issue location.
     * Both latitude and longitude are required.
     */
    @JsonProperty("location_coords")
    private LocationCoords locationCoords;

    /**
     * ISO 3166-1 alpha-2 country code.
     * Optional — auto-inferred from coordinates if omitted.
     * Valid values: BR, RU, IN, CN, ZA.
     */
    @JsonProperty("country_code")
    private String countryCode;

    /**
     * Channel through which the feedback was submitted.
     * Default: "api". Valid: api, web_form, sms, whatsapp, partner_import.
     */
    @JsonProperty("source_channel")
    private String sourceChannel;

    /**
     * Optional anonymous identifier for the submitter.
     * Must not contain personally identifiable information (PII).
     */
    @JsonProperty("submitter_id")
    private String submitterId;

    /** Default constructor required for Jackson deserialization. */
    public CitizenFeedbackRequest() {
    }

    // ========================================================================
    // Getters and Setters
    // ========================================================================

    /** @return the raw feedback text in the citizen's native language */
    public String getRawText() {
        return rawText;
    }

    /** @param rawText the raw feedback text (10–5000 characters) */
    public void setRawText(final String rawText) {
        this.rawText = rawText;
    }

    /** @return the ISO 639-1 language code */
    public String getLanguage() {
        return language;
    }

    /** @param language ISO 639-1 language code (e.g., "hi", "en") */
    public void setLanguage(final String language) {
        this.language = language;
    }

    /** @return the GPS coordinates of the issue location */
    public LocationCoords getLocationCoords() {
        return locationCoords;
    }

    /** @param locationCoords WGS 84 coordinates */
    public void setLocationCoords(final LocationCoords locationCoords) {
        this.locationCoords = locationCoords;
    }

    /** @return the ISO 3166-1 alpha-2 country code, or {@code null} */
    public String getCountryCode() {
        return countryCode;
    }

    /** @param countryCode ISO 3166-1 alpha-2 code (BR, RU, IN, CN, ZA) */
    public void setCountryCode(final String countryCode) {
        this.countryCode = countryCode;
    }

    /** @return the source channel identifier */
    public String getSourceChannel() {
        return sourceChannel;
    }

    /** @param sourceChannel one of: api, web_form, sms, whatsapp, partner_import */
    public void setSourceChannel(final String sourceChannel) {
        this.sourceChannel = sourceChannel;
    }

    /** @return the anonymous submitter identifier, or {@code null} */
    public String getSubmitterId() {
        return submitterId;
    }

    /** @param submitterId anonymous identifier (no PII) */
    public void setSubmitterId(final String submitterId) {
        this.submitterId = submitterId;
    }
}

package org.nagarikbrics.ingestion.service;

import com.fasterxml.jackson.databind.JsonNode;
import org.nagarikbrics.ingestion.exception.ValidationException;
import org.nagarikbrics.ingestion.model.ApiError;
import org.nagarikbrics.ingestion.model.CitizenFeedbackRecord;
import org.nagarikbrics.ingestion.model.CitizenFeedbackRequest;
import org.nagarikbrics.ingestion.model.LocationCoords;
import org.nagarikbrics.ingestion.validation.FeedbackValidator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Core service for processing citizen feedback submissions.
 *
 * <p>Orchestrates the full feedback processing pipeline:</p>
 * <ol>
 *   <li>Validate the incoming request via {@link FeedbackValidator}</li>
 *   <li>Generate a UUID and set defaults for optional fields</li>
 *   <li>Send to AI Core for NLP processing via {@link AiCoreClient}</li>
 *   <li>Build and store the enriched {@link CitizenFeedbackRecord}</li>
 * </ol>
 *
 * <h2>Storage</h2>
 * <p>For the MVP, records are stored in an in-memory {@link ConcurrentHashMap}.
 * This is intentionally simple — production would use a persistent store.
 * The map is thread-safe for concurrent submissions.</p>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
@Service
public class FeedbackService {

    private static final Logger LOG = LoggerFactory.getLogger(FeedbackService.class);

    /** In-memory feedback store (MVP — replace with DB in production). */
    private final Map<String, CitizenFeedbackRecord> feedbackStore = new ConcurrentHashMap<>();

    /** Input validator for feedback requests. */
    private final FeedbackValidator validator;

    /** HTTP client for AI Core communication. */
    private final AiCoreClient aiCoreClient;

    /**
     * Constructs the FeedbackService with its dependencies.
     *
     * @param validator    the feedback input validator
     * @param aiCoreClient the AI Core HTTP client
     */
    public FeedbackService(final FeedbackValidator validator,
                            final AiCoreClient aiCoreClient) {
        this.validator = validator;
        this.aiCoreClient = aiCoreClient;
    }

    /**
     * Processes a citizen feedback submission end-to-end.
     *
     * <p>This is the main entry point called by the controller. It validates
     * the request, assigns an ID, calls the AI Core for NLP enrichment,
     * and returns the fully processed record.</p>
     *
     * @param request the raw citizen feedback request
     * @return the fully processed and enriched feedback record
     * @throws ValidationException if the request fails validation
     * @throws org.nagarikbrics.ingestion.exception.AiCoreException if AI Core
     *         communication fails
     */
    public CitizenFeedbackRecord submitFeedback(final CitizenFeedbackRequest request) {
        // Step 1: Validate input
        final List<ApiError.FieldError> errors = validator.validate(request);
        if (!errors.isEmpty()) {
            // Check if the error is specifically about unsupported language
            final boolean hasLanguageError = errors.stream()
                    .anyMatch(e -> "language".equals(e.getField())
                            && e.getIssue() != null
                            && e.getIssue().contains("Unsupported"));

            final String errorCode = hasLanguageError
                    ? "UNSUPPORTED_LANGUAGE"
                    : "VALIDATION_FAILED";

            throw new ValidationException(
                    errorCode,
                    "Request payload failed schema validation.",
                    errors
            );
        }

        // Step 2: Generate UUID and record creation timestamp
        final String feedbackId = UUID.randomUUID().toString();
        final Instant createdAt = Instant.now();

        LOG.info("Processing feedback {} — language: {}, coords: ({}, {})",
                feedbackId, request.getLanguage(),
                request.getLocationCoords().getLat(),
                request.getLocationCoords().getLng());

        // Step 3: Apply defaults for optional fields
        final String sourceChannel = request.getSourceChannel() != null
                ? request.getSourceChannel()
                : "api";

        // Step 4: Send to AI Core for NLP processing
        final JsonNode aiResult = aiCoreClient.processFeedback(
                feedbackId,
                request.getRawText(),
                request.getLanguage(),
                request.getLocationCoords().getLat(),
                request.getLocationCoords().getLng(),
                request.getCountryCode()
        );

        // Step 5: Build enriched record from AI Core response
        final CitizenFeedbackRecord record = buildRecord(
                feedbackId, request, sourceChannel, createdAt, aiResult
        );

        // Step 6: Store the record
        feedbackStore.put(feedbackId, record);

        LOG.info("Feedback {} processed and stored. Category: {}, Urgency: {}",
                feedbackId, record.getCategory(), record.getUrgencyScore());

        return record;
    }

    /**
     * Retrieves all stored feedback records.
     *
     * <p>Used by the AI Core's hotspot analysis to access all feedback.
     * Returns records in no guaranteed order.</p>
     *
     * @return list of all stored feedback records
     */
    public List<CitizenFeedbackRecord> getAllFeedback() {
        return new ArrayList<>(feedbackStore.values());
    }

    /**
     * Returns the total count of stored feedback records.
     *
     * @return number of feedback records in the store
     */
    public int getFeedbackCount() {
        return feedbackStore.size();
    }

    /**
     * Builds a fully enriched {@link CitizenFeedbackRecord} from the
     * original request and the AI Core's NLP response.
     *
     * @param feedbackId    the assigned UUID
     * @param request       the original validated request
     * @param sourceChannel the resolved source channel
     * @param createdAt     the creation timestamp
     * @param aiResult      the AI Core's JSON response
     * @return the fully populated feedback record
     */
    private CitizenFeedbackRecord buildRecord(final String feedbackId,
                                               final CitizenFeedbackRequest request,
                                               final String sourceChannel,
                                               final Instant createdAt,
                                               final JsonNode aiResult) {
        final CitizenFeedbackRecord record = new CitizenFeedbackRecord();

        // Original fields
        record.setFeedbackId(feedbackId);
        record.setRawText(request.getRawText());
        record.setLanguage(request.getLanguage());
        record.setLocationCoords(new LocationCoords(
                request.getLocationCoords().getLat(),
                request.getLocationCoords().getLng()
        ));
        record.setCountryCode(
                request.getCountryCode() != null
                        ? request.getCountryCode()
                        : getTextOrDefault(aiResult, "country_code", "")
        );
        record.setSourceChannel(sourceChannel);
        record.setSubmitterId(request.getSubmitterId());

        // AI-enriched fields
        record.setTranslatedText(getTextOrDefault(aiResult, "translated_text", request.getRawText()));
        record.setSentiment(getTextOrDefault(aiResult, "sentiment", "neutral"));
        record.setSentimentScore(getDoubleOrDefault(aiResult, "sentiment_score", 0.0));
        record.setCategory(getTextOrDefault(aiResult, "category", "other"));
        record.setUrgencyScore(getDoubleOrDefault(aiResult, "urgency_score", 5.0));
        record.setRegionName(getTextOrDefault(aiResult, "region_name", "Unknown"));

        // Extract keywords array
        final List<String> keywords = new ArrayList<>();
        if (aiResult.has("keywords") && aiResult.get("keywords").isArray()) {
            aiResult.get("keywords").forEach(node -> keywords.add(node.asText()));
        }
        record.setKeywords(keywords);

        // Timestamps and status
        record.setCreatedAt(createdAt);
        record.setProcessedAt(Instant.now());
        record.setStatus("processed");

        return record;
    }

    /**
     * Safely extracts a text value from a JsonNode, returning a default
     * if the field is missing or null.
     *
     * @param node         the JSON node to read from
     * @param fieldName    the field name to extract
     * @param defaultValue the fallback value
     * @return the extracted text or the default
     */
    private String getTextOrDefault(final JsonNode node,
                                     final String fieldName,
                                     final String defaultValue) {
        if (node != null && node.has(fieldName) && !node.get(fieldName).isNull()) {
            return node.get(fieldName).asText();
        }
        return defaultValue;
    }

    /**
     * Safely extracts a double value from a JsonNode, returning a default
     * if the field is missing or null.
     *
     * @param node         the JSON node to read from
     * @param fieldName    the field name to extract
     * @param defaultValue the fallback value
     * @return the extracted double or the default
     */
    private double getDoubleOrDefault(final JsonNode node,
                                       final String fieldName,
                                       final double defaultValue) {
        if (node != null && node.has(fieldName) && !node.get(fieldName).isNull()) {
            return node.get(fieldName).asDouble(defaultValue);
        }
        return defaultValue;
    }
}

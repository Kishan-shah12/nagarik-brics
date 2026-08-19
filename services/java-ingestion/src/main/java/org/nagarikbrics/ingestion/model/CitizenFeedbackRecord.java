package org.nagarikbrics.ingestion.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.List;

/**
 * Fully processed citizen feedback record.
 *
 * <p>This is the enriched data object returned after the Java Ingestion
 * service validates the raw feedback and the Python AI Core processes it
 * through the Gemini NLP pipeline. It contains all original fields plus
 * AI-extracted insights.</p>
 *
 * <h2>AI-Enriched Fields</h2>
 * <ul>
 *   <li>{@code translated_text} — English translation (via Gemini)</li>
 *   <li>{@code sentiment} — Categorical sentiment label</li>
 *   <li>{@code sentiment_score} — Continuous sentiment score [-1.0, 1.0]</li>
 *   <li>{@code category} — Infrastructure category classification</li>
 *   <li>{@code urgency_score} — AI-assessed urgency [0, 10]</li>
 *   <li>{@code keywords} — Key terms for search and clustering</li>
 * </ul>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 * @see CitizenFeedbackRequest
 */
public class CitizenFeedbackRecord {

    /** Unique identifier for this feedback record (UUID v4). */
    @JsonProperty("feedback_id")
    private String feedbackId;

    /** Original citizen feedback text, unmodified. */
    @JsonProperty("raw_text")
    private String rawText;

    /** ISO 639-1 language code of the original text. */
    @JsonProperty("language")
    private String language;

    /**
     * English translation of raw_text produced by Gemini.
     * Identical to raw_text if language is 'en'.
     */
    @JsonProperty("translated_text")
    private String translatedText;

    /** GPS coordinates of the infrastructure issue location. */
    @JsonProperty("location_coords")
    private LocationCoords locationCoords;

    /** ISO 3166-1 alpha-2 country code. */
    @JsonProperty("country_code")
    private String countryCode;

    /** Human-readable region/state/province name. */
    @JsonProperty("region_name")
    private String regionName;

    /**
     * Sentiment classification by Gemini.
     * One of: very_negative, negative, neutral, positive, very_positive.
     */
    @JsonProperty("sentiment")
    private String sentiment;

    /**
     * Continuous sentiment score.
     * Range: -1.0 (extremely negative) to +1.0 (extremely positive).
     */
    @JsonProperty("sentiment_score")
    private Double sentimentScore;

    /**
     * Infrastructure category classified by Gemini.
     * One of: water_sanitation, transportation, energy_power, healthcare,
     * education, housing, digital_connectivity, waste_management,
     * public_safety, other.
     */
    @JsonProperty("category")
    private String category;

    /**
     * AI-assessed urgency score.
     * Range: 0 (informational) to 10 (life-threatening emergency).
     */
    @JsonProperty("urgency_score")
    private Double urgencyScore;

    /** Key terms extracted by Gemini for search and clustering. */
    @JsonProperty("keywords")
    private List<String> keywords;

    /** Channel through which the feedback was submitted. */
    @JsonProperty("source_channel")
    private String sourceChannel;

    /** Anonymous submitter identifier. */
    @JsonProperty("submitter_id")
    private String submitterId;

    /**
     * Processing pipeline status.
     * One of: received, processing, processed, failed.
     */
    @JsonProperty("status")
    private String status;

    /** ISO 8601 timestamp of when the feedback was received. */
    @JsonProperty("created_at")
    private Instant createdAt;

    /** ISO 8601 timestamp of when AI processing completed. Null if pending. */
    @JsonProperty("processed_at")
    private Instant processedAt;

    /** Default constructor required for Jackson deserialization. */
    public CitizenFeedbackRecord() {
    }

    // ========================================================================
    // Getters and Setters
    // ========================================================================

    /** @return the unique feedback record identifier */
    public String getFeedbackId() {
        return feedbackId;
    }

    /** @param feedbackId UUID v4 identifier */
    public void setFeedbackId(final String feedbackId) {
        this.feedbackId = feedbackId;
    }

    /** @return the original unmodified feedback text */
    public String getRawText() {
        return rawText;
    }

    /** @param rawText original citizen feedback text */
    public void setRawText(final String rawText) {
        this.rawText = rawText;
    }

    /** @return the ISO 639-1 language code */
    public String getLanguage() {
        return language;
    }

    /** @param language ISO 639-1 language code */
    public void setLanguage(final String language) {
        this.language = language;
    }

    /** @return the English translation produced by Gemini */
    public String getTranslatedText() {
        return translatedText;
    }

    /** @param translatedText English translation */
    public void setTranslatedText(final String translatedText) {
        this.translatedText = translatedText;
    }

    /** @return the GPS coordinates of the issue */
    public LocationCoords getLocationCoords() {
        return locationCoords;
    }

    /** @param locationCoords WGS 84 coordinates */
    public void setLocationCoords(final LocationCoords locationCoords) {
        this.locationCoords = locationCoords;
    }

    /** @return the ISO 3166-1 alpha-2 country code */
    public String getCountryCode() {
        return countryCode;
    }

    /** @param countryCode ISO 3166-1 alpha-2 code */
    public void setCountryCode(final String countryCode) {
        this.countryCode = countryCode;
    }

    /** @return the human-readable region name */
    public String getRegionName() {
        return regionName;
    }

    /** @param regionName state/province/district name */
    public void setRegionName(final String regionName) {
        this.regionName = regionName;
    }

    /** @return the categorical sentiment label */
    public String getSentiment() {
        return sentiment;
    }

    /** @param sentiment one of: very_negative, negative, neutral, positive, very_positive */
    public void setSentiment(final String sentiment) {
        this.sentiment = sentiment;
    }

    /** @return the continuous sentiment score [-1.0, 1.0] */
    public Double getSentimentScore() {
        return sentimentScore;
    }

    /** @param sentimentScore continuous score from -1.0 to 1.0 */
    public void setSentimentScore(final Double sentimentScore) {
        this.sentimentScore = sentimentScore;
    }

    /** @return the infrastructure category */
    public String getCategory() {
        return category;
    }

    /** @param category infrastructure category enum value */
    public void setCategory(final String category) {
        this.category = category;
    }

    /** @return the urgency score [0, 10] */
    public Double getUrgencyScore() {
        return urgencyScore;
    }

    /** @param urgencyScore AI-assessed urgency from 0 to 10 */
    public void setUrgencyScore(final Double urgencyScore) {
        this.urgencyScore = urgencyScore;
    }

    /** @return list of extracted keywords */
    public List<String> getKeywords() {
        return keywords;
    }

    /** @param keywords key terms for search and clustering */
    public void setKeywords(final List<String> keywords) {
        this.keywords = keywords;
    }

    /** @return the source channel identifier */
    public String getSourceChannel() {
        return sourceChannel;
    }

    /** @param sourceChannel submission channel */
    public void setSourceChannel(final String sourceChannel) {
        this.sourceChannel = sourceChannel;
    }

    /** @return the anonymous submitter identifier */
    public String getSubmitterId() {
        return submitterId;
    }

    /** @param submitterId anonymous identifier */
    public void setSubmitterId(final String submitterId) {
        this.submitterId = submitterId;
    }

    /** @return the processing pipeline status */
    public String getStatus() {
        return status;
    }

    /** @param status one of: received, processing, processed, failed */
    public void setStatus(final String status) {
        this.status = status;
    }

    /** @return the creation timestamp */
    public Instant getCreatedAt() {
        return createdAt;
    }

    /** @param createdAt ISO 8601 creation timestamp */
    public void setCreatedAt(final Instant createdAt) {
        this.createdAt = createdAt;
    }

    /** @return the processing completion timestamp, or null */
    public Instant getProcessedAt() {
        return processedAt;
    }

    /** @param processedAt ISO 8601 processing completion timestamp */
    public void setProcessedAt(final Instant processedAt) {
        this.processedAt = processedAt;
    }
}

package org.nagarikbrics.ingestion.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;

/**
 * Request metadata included in every API response.
 *
 * <p>Provides traceability and observability information for every request
 * processed by the ingestion service. The {@code request_id} enables
 * end-to-end request tracing across microservices.</p>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiMeta {

    /** Unique request identifier for distributed tracing (UUID v4). */
    @JsonProperty("request_id")
    private String requestId;

    /** ISO 8601 UTC timestamp of when the response was generated. */
    @JsonProperty("timestamp")
    private Instant timestamp;

    /**
     * Total processing time in milliseconds.
     * Null for error responses where timing is not meaningful.
     */
    @JsonProperty("processing_time_ms")
    private Long processingTimeMs;

    /** Default constructor. */
    public ApiMeta() {
    }

    /**
     * Constructs metadata with all fields.
     *
     * @param requestId        unique request identifier
     * @param timestamp        response generation timestamp
     * @param processingTimeMs processing duration in ms (may be null)
     */
    public ApiMeta(final String requestId, final Instant timestamp, final Long processingTimeMs) {
        this.requestId = requestId;
        this.timestamp = timestamp;
        this.processingTimeMs = processingTimeMs;
    }

    /** @return the unique request identifier */
    public String getRequestId() {
        return requestId;
    }

    /** @return the response generation timestamp */
    public Instant getTimestamp() {
        return timestamp;
    }

    /** @return the processing time in milliseconds, or null */
    public Long getProcessingTimeMs() {
        return processingTimeMs;
    }
}

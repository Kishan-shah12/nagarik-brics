package org.nagarikbrics.ingestion.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;

/**
 * Standard API response envelope for all endpoints.
 *
 * <p>Every response from the Java Ingestion service is wrapped in this
 * envelope to ensure consistent structure across the NagarikBRICS platform.
 * Both success and error responses use this same top-level structure.</p>
 *
 * <h2>Success Response</h2>
 * <pre>{@code
 * {
 *   "status": "success",
 *   "data": { ... },
 *   "meta": { "request_id": "...", "timestamp": "...", "processing_time_ms": 142 }
 * }
 * }</pre>
 *
 * <h2>Error Response</h2>
 * <pre>{@code
 * {
 *   "status": "error",
 *   "error": { "code": "...", "message": "...", "details": [...] },
 *   "meta": { "request_id": "...", "timestamp": "..." }
 * }
 * }</pre>
 *
 * @param <T> the type of the data payload (for success responses)
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiResponse<T> {

    /** Response status: "success" or "error". */
    @JsonProperty("status")
    private String status;

    /** The response data payload. Null for error responses. */
    @JsonProperty("data")
    private T data;

    /** Error details. Null for success responses. */
    @JsonProperty("error")
    private ApiError error;

    /** Request metadata (request_id, timestamp, processing_time_ms). */
    @JsonProperty("meta")
    private ApiMeta meta;

    /** Default constructor required for Jackson. */
    public ApiResponse() {
    }

    /**
     * Creates a success response with the given data payload.
     *
     * @param <T>              the data type
     * @param data             the response payload
     * @param requestId        unique request identifier (UUID v4)
     * @param processingTimeMs time taken to process the request in milliseconds
     * @return a fully constructed success response
     */
    public static <T> ApiResponse<T> success(final T data,
                                              final String requestId,
                                              final long processingTimeMs) {
        final ApiResponse<T> response = new ApiResponse<>();
        response.status = "success";
        response.data = data;
        response.meta = new ApiMeta(requestId, Instant.now(), processingTimeMs);
        return response;
    }

    /**
     * Creates an error response with the given error details.
     *
     * @param <T>       the data type (always {@code Void} for errors)
     * @param error     the error details object
     * @param requestId unique request identifier (UUID v4)
     * @return a fully constructed error response
     */
    public static <T> ApiResponse<T> error(final ApiError error,
                                            final String requestId) {
        final ApiResponse<T> response = new ApiResponse<>();
        response.status = "error";
        response.error = error;
        response.meta = new ApiMeta(requestId, Instant.now(), null);
        return response;
    }

    // ========================================================================
    // Getters
    // ========================================================================

    /** @return "success" or "error" */
    public String getStatus() {
        return status;
    }

    /** @return the data payload, or null for error responses */
    public T getData() {
        return data;
    }

    /** @return the error details, or null for success responses */
    public ApiError getError() {
        return error;
    }

    /** @return the request metadata */
    public ApiMeta getMeta() {
        return meta;
    }
}

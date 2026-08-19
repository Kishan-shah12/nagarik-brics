package org.nagarikbrics.ingestion.exception;

import org.nagarikbrics.ingestion.model.ApiError;
import org.nagarikbrics.ingestion.model.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.UUID;

/**
 * Global exception handler for the ingestion service.
 *
 * <p>Intercepts all exceptions thrown by controllers and services, and
 * converts them into standardized {@link ApiResponse} error envelopes.
 * This ensures that clients NEVER receive raw Spring error responses
 * or stack traces.</p>
 *
 * <h2>Handled Exceptions</h2>
 * <ul>
 *   <li>{@link ValidationException} → 400 with field-level details</li>
 *   <li>{@link HttpMessageNotReadableException} → 400 for malformed JSON</li>
 *   <li>{@link AiCoreException} → 500 for AI Core communication failures</li>
 *   <li>{@link Exception} → 500 catch-all for unexpected errors</li>
 * </ul>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger LOG = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * Handles validation failures with detailed field-level error reporting.
     *
     * @param ex the validation exception
     * @return 400 response with structured error details
     */
    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidation(final ValidationException ex) {
        LOG.warn("Validation failed: {} — {} field errors",
                ex.getMessage(), ex.getFieldErrors().size());

        final ApiError error = new ApiError(
                ex.getErrorCode(),
                ex.getMessage(),
                ex.getFieldErrors()
        );
        final ApiResponse<Void> response = ApiResponse.error(
                error, UUID.randomUUID().toString()
        );
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
    }

    /**
     * Handles malformed JSON request bodies.
     *
     * <p>Triggered when Jackson cannot deserialize the request body
     * (e.g., invalid JSON syntax, wrong types).</p>
     *
     * @param ex the message not readable exception
     * @return 400 response indicating malformed JSON
     */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiResponse<Void>> handleMalformedJson(
            final HttpMessageNotReadableException ex) {
        LOG.warn("Malformed JSON request: {}", ex.getMessage());

        final ApiError error = new ApiError(
                "VALIDATION_FAILED",
                "Request body contains malformed JSON. Please verify syntax."
        );
        final ApiResponse<Void> response = ApiResponse.error(
                error, UUID.randomUUID().toString()
        );
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
    }

    /**
     * Handles AI Core communication failures.
     *
     * @param ex the AI Core exception
     * @return 500 response indicating processing failure
     */
    @ExceptionHandler(AiCoreException.class)
    public ResponseEntity<ApiResponse<Void>> handleAiCoreFailure(
            final AiCoreException ex) {
        LOG.error("AI Core processing failed: {}", ex.getMessage(), ex);

        final ApiError error = new ApiError(
                "PROCESSING_FAILED",
                "AI processing service is temporarily unavailable. Please retry."
        );
        final ApiResponse<Void> response = ApiResponse.error(
                error, UUID.randomUUID().toString()
        );
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }

    /**
     * Catch-all handler for unexpected exceptions.
     *
     * <p>Logs the full stack trace for debugging but returns only
     * a generic error message to the client (no information leakage).</p>
     *
     * @param ex the unexpected exception
     * @return 500 response with generic error message
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleUnexpected(final Exception ex) {
        LOG.error("Unexpected error processing request", ex);

        final ApiError error = new ApiError(
                "PROCESSING_FAILED",
                "An unexpected error occurred. Please contact support."
        );
        final ApiResponse<Void> response = ApiResponse.error(
                error, UUID.randomUUID().toString()
        );
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }
}

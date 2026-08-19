package org.nagarikbrics.ingestion.exception;

import org.nagarikbrics.ingestion.model.ApiError;

import java.util.List;

/**
 * Custom exception for feedback validation failures.
 *
 * <p>Thrown by the service layer when the {@link org.nagarikbrics.ingestion.validation.FeedbackValidator}
 * detects one or more validation errors in the incoming request. Carries
 * the full list of field-level errors for inclusion in the API error response.</p>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
public class ValidationException extends RuntimeException {

    /** The machine-readable error code for this validation failure. */
    private final String errorCode;

    /** The list of field-level validation errors. */
    private final List<ApiError.FieldError> fieldErrors;

    /**
     * Constructs a ValidationException with all error details.
     *
     * @param errorCode   machine-readable error code (e.g., "VALIDATION_FAILED")
     * @param message     human-readable summary message
     * @param fieldErrors list of field-level validation issues
     */
    public ValidationException(final String errorCode,
                                final String message,
                                final List<ApiError.FieldError> fieldErrors) {
        super(message);
        this.errorCode = errorCode;
        this.fieldErrors = fieldErrors;
    }

    /**
     * Returns the machine-readable error code.
     *
     * @return error code string (e.g., "VALIDATION_FAILED")
     */
    public String getErrorCode() {
        return errorCode;
    }

    /**
     * Returns the list of field-level validation errors.
     *
     * @return immutable list of field errors
     */
    public List<ApiError.FieldError> getFieldErrors() {
        return fieldErrors;
    }
}

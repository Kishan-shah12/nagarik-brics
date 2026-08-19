package org.nagarikbrics.ingestion.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Standard error detail object for API error responses.
 *
 * <p>Contains a machine-readable error code, a human-readable message,
 * and an optional list of field-level validation details.</p>
 *
 * <h2>Error Codes</h2>
 * <ul>
 *   <li>{@code VALIDATION_FAILED} — Request payload failed schema validation</li>
 *   <li>{@code UNSUPPORTED_LANGUAGE} — Language code not in supported set</li>
 *   <li>{@code COORDS_OUT_OF_RANGE} — Coordinates outside valid range</li>
 *   <li>{@code PROCESSING_FAILED} — AI Core unreachable or Gemini error</li>
 *   <li>{@code RATE_LIMIT_EXCEEDED} — Too many requests</li>
 * </ul>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiError {

    /** Machine-readable error code (e.g., "VALIDATION_FAILED"). */
    @JsonProperty("code")
    private String code;

    /** Human-readable error description. */
    @JsonProperty("message")
    private String message;

    /**
     * Optional list of field-level validation issues.
     * Each detail specifies which field failed and why.
     */
    @JsonProperty("details")
    private List<FieldError> details;

    /** Default constructor. */
    public ApiError() {
    }

    /**
     * Constructs an error with code, message, and optional field details.
     *
     * @param code    machine-readable error code
     * @param message human-readable description
     * @param details field-level validation errors (may be null)
     */
    public ApiError(final String code, final String message, final List<FieldError> details) {
        this.code = code;
        this.message = message;
        this.details = details;
    }

    /**
     * Constructs an error with code and message only (no field details).
     *
     * @param code    machine-readable error code
     * @param message human-readable description
     */
    public ApiError(final String code, final String message) {
        this(code, message, null);
    }

    /** @return the machine-readable error code */
    public String getCode() {
        return code;
    }

    /** @return the human-readable error description */
    public String getMessage() {
        return message;
    }

    /** @return the list of field-level validation errors, or null */
    public List<FieldError> getDetails() {
        return details;
    }

    // ========================================================================
    // Nested class: FieldError
    // ========================================================================

    /**
     * Represents a single field-level validation error.
     *
     * <p>Example:</p>
     * <pre>{@code
     * { "field": "raw_text", "issue": "Must be at least 10 characters. Received 4." }
     * }</pre>
     */
    public static class FieldError {

        /** The name of the field that failed validation. */
        @JsonProperty("field")
        private String field;

        /** Human-readable description of the validation failure. */
        @JsonProperty("issue")
        private String issue;

        /** Default constructor. */
        public FieldError() {
        }

        /**
         * Constructs a field error.
         *
         * @param field the field name (e.g., "raw_text")
         * @param issue the validation failure description
         */
        public FieldError(final String field, final String issue) {
            this.field = field;
            this.issue = issue;
        }

        /** @return the field name */
        public String getField() {
            return field;
        }

        /** @return the validation issue description */
        public String getIssue() {
            return issue;
        }
    }
}

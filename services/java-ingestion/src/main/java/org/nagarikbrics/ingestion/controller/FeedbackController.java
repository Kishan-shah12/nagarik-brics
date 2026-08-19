package org.nagarikbrics.ingestion.controller;

import org.nagarikbrics.ingestion.model.ApiResponse;
import org.nagarikbrics.ingestion.model.CitizenFeedbackRecord;
import org.nagarikbrics.ingestion.model.CitizenFeedbackRequest;
import org.nagarikbrics.ingestion.service.FeedbackService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

/**
 * REST controller for citizen feedback ingestion.
 *
 * <p>Exposes the {@code POST /api/v1/feedback/submit} endpoint as defined
 * in the API contract (api-docs.md). This is the primary entry point for
 * citizen feedback into the NagarikBRICS platform.</p>
 *
 * <h2>Endpoint Summary</h2>
 * <table>
 *   <tr><th>Method</th><th>Path</th><th>Description</th></tr>
 *   <tr><td>POST</td><td>/api/v1/feedback/submit</td><td>Submit citizen feedback</td></tr>
 *   <tr><td>GET</td><td>/api/v1/feedback/all</td><td>Retrieve all feedback (internal)</td></tr>
 * </table>
 *
 * <h2>CORS</h2>
 * <p>Cross-origin requests are allowed from any origin for the MVP.
 * Production deployments MUST restrict this to the frontend domain.</p>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 * @see FeedbackService
 * @see org.nagarikbrics.ingestion.exception.GlobalExceptionHandler
 */
@RestController
@RequestMapping("/api/v1/feedback")
@CrossOrigin(origins = "*") // MVP: Open CORS. Restrict in production.
public class FeedbackController {

    private static final Logger LOG = LoggerFactory.getLogger(FeedbackController.class);

    /** The core feedback processing service. */
    private final FeedbackService feedbackService;

    /**
     * Constructs the controller with its service dependency.
     *
     * @param feedbackService the feedback processing service
     */
    public FeedbackController(final FeedbackService feedbackService) {
        this.feedbackService = feedbackService;
    }

    /**
     * Submits citizen feedback for processing.
     *
     * <p>Accepts raw citizen feedback in any supported BRICS language,
     * validates the payload, sends it to the AI Core for NLP processing,
     * and returns the fully enriched feedback record.</p>
     *
     * <h3>Request Example</h3>
     * <pre>{@code
     * POST /api/v1/feedback/submit
     * Content-Type: application/json
     *
     * {
     *   "raw_text": "हमारे गाँव में पानी नहीं आ रहा है।",
     *   "language": "hi",
     *   "location_coords": { "lat": 26.8467, "lng": 80.9462 }
     * }
     * }</pre>
     *
     * <h3>Response (201 Created)</h3>
     * <p>Returns the fully processed feedback record wrapped in the
     * standard {@link ApiResponse} envelope with status "success".</p>
     *
     * <h3>Error Responses</h3>
     * <ul>
     *   <li>400 — VALIDATION_FAILED, UNSUPPORTED_LANGUAGE, COORDS_OUT_OF_RANGE</li>
     *   <li>500 — PROCESSING_FAILED (AI Core unreachable)</li>
     * </ul>
     *
     * @param request   the citizen feedback request body
     * @param requestId optional X-Request-Id header for distributed tracing;
     *                  auto-generated (UUID v4) if not provided
     * @return 201 response with the enriched feedback record
     */
    @PostMapping(
            value = "/submit",
            consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<ApiResponse<CitizenFeedbackRecord>> submitFeedback(
            @RequestBody final CitizenFeedbackRequest request,
            @RequestHeader(value = "X-Request-Id", required = false) final String requestId) {

        final long startTime = System.currentTimeMillis();

        // Resolve or generate the request ID for tracing
        final String resolvedRequestId = (requestId != null && !requestId.isBlank())
                ? requestId
                : UUID.randomUUID().toString();

        LOG.info("Received feedback submission — Request-ID: {}", resolvedRequestId);

        // Delegate to the service layer (validation + AI Core + storage)
        final CitizenFeedbackRecord record = feedbackService.submitFeedback(request);

        // Calculate processing time
        final long processingTimeMs = System.currentTimeMillis() - startTime;

        LOG.info("Feedback {} processed in {}ms — Request-ID: {}",
                record.getFeedbackId(), processingTimeMs, resolvedRequestId);

        // Build success response envelope
        final ApiResponse<CitizenFeedbackRecord> response = ApiResponse.success(
                record, resolvedRequestId, processingTimeMs
        );

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(response);
    }

    /**
     * Retrieves all stored feedback records.
     *
     * <p>Internal endpoint used by the Python AI Core and frontend dashboard
     * to access aggregated feedback data. Not part of the public API contract
     * but useful for the MVP demo.</p>
     *
     * @param requestId optional X-Request-Id header for tracing
     * @return 200 response with list of all feedback records
     */
    @GetMapping(
            value = "/all",
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<ApiResponse<List<CitizenFeedbackRecord>>> getAllFeedback(
            @RequestHeader(value = "X-Request-Id", required = false) final String requestId) {

        final long startTime = System.currentTimeMillis();
        final String resolvedRequestId = (requestId != null && !requestId.isBlank())
                ? requestId
                : UUID.randomUUID().toString();

        final List<CitizenFeedbackRecord> records = feedbackService.getAllFeedback();
        final long processingTimeMs = System.currentTimeMillis() - startTime;

        LOG.info("Retrieved {} feedback records in {}ms", records.size(), processingTimeMs);

        final ApiResponse<List<CitizenFeedbackRecord>> response = ApiResponse.success(
                records, resolvedRequestId, processingTimeMs
        );

        return ResponseEntity.ok(response);
    }
}

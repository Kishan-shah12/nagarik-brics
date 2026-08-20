# ==============================================================================
# NagarikBRICS — Java Ingestion Service (Multi-Stage Build)
# ==============================================================================
# Stage 1: Build with Maven on full JDK
# Stage 2: Run on minimal JRE (eclipse-temurin:21-jre-alpine)
#
# SECURITY: Runs as non-root 'appuser' (UID 1001)
# SIZE TARGET: Final image < 200 MB
# ==============================================================================

# --------------------------------------------------------------------------
# STAGE 1: BUILD
# --------------------------------------------------------------------------
FROM eclipse-temurin:21-jdk-alpine AS builder

# Install Maven (Alpine package — no wrapper binaries needed)
RUN apk add --no-cache maven

WORKDIR /build

# Copy POM first for dependency caching
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source and build
COPY src/ src/
RUN mvn clean package -DskipTests -B \
    && mv target/ingestion-service.jar /build/app.jar

# --------------------------------------------------------------------------
# STAGE 2: RUN
# --------------------------------------------------------------------------
FROM eclipse-temurin:21-jre-alpine AS runtime

# Security: Create non-root user
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup appuser

WORKDIR /app

# Copy only the compiled JAR from build stage
COPY --from=builder /build/app.jar app.jar

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose service port (matches docker-compose.yml)
EXPOSE 8081

# JVM tuning for container environment
ENV JAVA_OPTS="-Xmx256m -Xms128m -XX:+UseContainerSupport -XX:MaxRAMPercentage=50.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD wget --quiet --tries=1 --spider http://localhost:8081/actuator/health || exit 1

# Run the application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

package org.nagarikbrics.ingestion.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * GPS coordinates representing the location of an infrastructure issue.
 *
 * <p>Coordinates use the WGS 84 geodetic datum (EPSG:4326), the standard
 * used by GPS systems worldwide. Values are expressed in decimal degrees.</p>
 *
 * <h2>Validation Constraints</h2>
 * <ul>
 *   <li>{@code lat} must be in range [-90.0, 90.0]</li>
 *   <li>{@code lng} must be in range [-180.0, 180.0]</li>
 *   <li>Both fields are required (non-null)</li>
 * </ul>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
public class LocationCoords {

    /**
     * Latitude in decimal degrees (WGS 84).
     * Valid range: -90.0 (South Pole) to 90.0 (North Pole).
     */
    @JsonProperty("lat")
    private Double lat;

    /**
     * Longitude in decimal degrees (WGS 84).
     * Valid range: -180.0 (International Date Line West) to 180.0 (East).
     */
    @JsonProperty("lng")
    private Double lng;

    /** Default constructor required for Jackson deserialization. */
    public LocationCoords() {
    }

    /**
     * Constructs a LocationCoords with the specified latitude and longitude.
     *
     * @param lat latitude in decimal degrees [-90.0, 90.0]
     * @param lng longitude in decimal degrees [-180.0, 180.0]
     */
    public LocationCoords(final Double lat, final Double lng) {
        this.lat = lat;
        this.lng = lng;
    }

    /**
     * Returns the latitude component.
     *
     * @return latitude in decimal degrees, or {@code null} if not set
     */
    public Double getLat() {
        return lat;
    }

    /**
     * Sets the latitude component.
     *
     * @param lat latitude in decimal degrees [-90.0, 90.0]
     */
    public void setLat(final Double lat) {
        this.lat = lat;
    }

    /**
     * Returns the longitude component.
     *
     * @return longitude in decimal degrees, or {@code null} if not set
     */
    public Double getLng() {
        return lng;
    }

    /**
     * Sets the longitude component.
     *
     * @param lng longitude in decimal degrees [-180.0, 180.0]
     */
    public void setLng(final Double lng) {
        this.lng = lng;
    }

    @Override
    public String toString() {
        return "LocationCoords{lat=" + lat + ", lng=" + lng + "}";
    }
}

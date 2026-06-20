package com.cavesketch.app.bridge

fun interface SatelliteBridge {
    /** Calls satellite_bridge.generate_satellite_map; returns its JSON result string. */
    suspend fun generateSatellite(inputsJson: String, workDir: String): String
}

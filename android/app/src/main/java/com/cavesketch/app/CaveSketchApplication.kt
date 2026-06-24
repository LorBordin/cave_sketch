package com.cavesketch.app

import android.app.Application
import android.util.Log
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class CaveSketchApplication : Application() {
    val initState = AppInitState()

    override fun onCreate() {
        super.onCreate()

        // Last-resort logger so an unexpected crash leaves a breadcrumb.
        val previous = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            Log.e("CaveSketch", "Uncaught exception on ${thread.name}", throwable)
            previous?.uncaughtException(thread, throwable)
        }

        // Per-session cleanup: remove last run's intermediate + output files.
        val present = filesDir.list()?.toList() ?: emptyList()
        com.cavesketch.app.util.filesToDelete(present).forEach {
            java.io.File(filesDir, it).delete()
        }

        // Start + pre-warm the Python runtime off the UI thread; publish readiness.
        Thread {
            try {
                if (!Python.isStarted()) {
                    Python.start(AndroidPlatform(this))
                }
                // Pay the one-time heavy import + matplotlib font-cache cost here.
                Python.getInstance().getModule("survey_bridge").callAttr("prewarm")
                initState.markReady()
            } catch (t: Throwable) {
                Log.e("CaveSketch", "Python init failed", t)
                initState.markFailed(com.cavesketch.app.util.friendlyError(t))
            }
        }.start()
    }
}

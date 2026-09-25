// EduPredict AI Global Runtime Configuration
// In production, when deployed on Vercel, requests to /api/* are automatically
// proxied via vercel.json rewrites or can point directly to the Render backend URL.
window.__ENV__ = window.__ENV__ || {
    API_URL: localStorage.getItem("EDUPREDICT_API_URL") || ""
};

// Expose helper to set backend URL dynamically if needed
window.setBackendUrl = function(url) {
    if (url) {
        localStorage.setItem("EDUPREDICT_API_URL", url.replace(/\/+$/, ''));
        window.__ENV__.API_URL = url.replace(/\/+$/, '');
        console.log("EduPredict Backend URL set to:", window.__ENV__.API_URL);
    } else {
        localStorage.removeItem("EDUPREDICT_API_URL");
        window.__ENV__.API_URL = "";
        console.log("EduPredict Backend URL reset to default origin");
    }
    if (typeof checkDatabaseHealth === 'function') {
        checkDatabaseHealth();
    }
};

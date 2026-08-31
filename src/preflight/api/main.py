from __future__ import annotations

import os
import uvicorn


def run():
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("preflight.api.app:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    run()

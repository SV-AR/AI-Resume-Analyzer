import { useCallback, useEffect, useState } from "react";
import { errorMessage } from "../services/api";

/** Runs an async loader on mount (and on `reload`) and tracks loading / error state. */
export function useAsync(loader, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const run = useCallback(() => {
    setLoading(true);
    setError("");
    return loader()
      .then(setData)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    run();
  }, [run]);

  return { data, error, loading, reload: run };
}

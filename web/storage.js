// Safe access to localStorage for store.py.
//
// MicroPython's FFI cannot catch an exception thrown by a JS function: it
// unwinds through the wasm instead of becoming a Python exception. So the
// calls that may throw (blocked, full or missing storage) are made here, in
// JS, and failures become plain return values. All JSON and shape checks
// stay in store.py.
globalThis.hexxleStorage = {
  get(key) {
    try {
      return globalThis.localStorage.getItem(key);
    } catch (error) {
      return null;
    }
  },
  set(key, value) {
    try {
      globalThis.localStorage.setItem(key, value);
      return true;
    } catch (error) {
      return false;
    }
  },
};

import '@testing-library/jest-dom';

// Global test setup
(global as any).matchMedia = (query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: () => {},
  removeListener: () => {},
  addEventListener: () => {},
  removeEventListener: () => {},
  dispatchEvent: () => {},
});

(global as any).ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

(global as any).IntersectionObserver = class {
  observe() {}
  disconnect() {}
};

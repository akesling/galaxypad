const rust = import('./pkg');

rust
  .then(m => m.start_galaxy_pad())
  .catch(console.error);

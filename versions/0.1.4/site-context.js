// Each browser origin owns a separate journal, lock and device permission.
// This acknowledgement cannot inspect or clear another origin's history.
export class SiteContext {
  constructor(hostname) {
    this.hosted = !['localhost', '127.0.0.1', '[::1]'].includes(hostname);
    this.confirmed = false;
  }
  get ready() { return !this.hosted || this.confirmed; }
  confirm(value) { this.confirmed = value === true; }
  reset() { this.confirmed = false; }
}

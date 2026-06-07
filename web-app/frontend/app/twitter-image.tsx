/**
 * Twitter/X card image (App Router file convention).
 *
 * Re-uses the Open Graph card so the brand image stays in one place. Next reads
 * the default export plus the `size` / `contentType` / `alt` segment exports.
 */
export { default, size, contentType, alt } from "./opengraph-image"

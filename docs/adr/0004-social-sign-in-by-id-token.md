# Social sign-in verifies the client's ID token and links by verified email

Google and Apple sign-in happen natively in the (Flutter) client, which sends
the provider's ID token; the backend checks it against the provider's public keys
and issues its own access and refresh tokens. There is no browser redirect flow,
which is why GitHub (no ID tokens) is left out. A sign-in whose verified email
matches an existing user links to that user as a linked identity; an unverified
email is refused rather than linked, since linking it would let anyone who
controls a provider account take over the user.

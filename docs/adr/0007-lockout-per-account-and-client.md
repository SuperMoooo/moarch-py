# Lockout counts per account and client, with an account-wide ceiling

Counting wrong passwords per account alone lets anyone who knows an email
lock its owner out, again and again, by typing wrong passwords on purpose. So
failures are counted per (account, client IP): five in a row lock that
account *for that client only*, and the owner signs in from theirs. Guessing
spread over many addresses is still stopped: fifty failures from all clients
within an hour lock the account itself, and a successful sign-in does not
reset that count (it would hand the guesser a fresh allowance). IPs are
stored as SHA-256 hashes. Rejected: per account only (the lock-out abuse
above), and slowing down without ever locking (a determined attacker could
still make sign-in unusable).

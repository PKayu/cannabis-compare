export default function PrivacyPage() {
  return (
    <main className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>

      <p className="text-sm text-gray-500 mb-8">Last updated: April 2026</p>

      <section className="space-y-6 text-gray-700">
        <div>
          <h2 className="text-xl font-semibold mb-2">1. Information We Collect</h2>
          <p>We collect only what is necessary to provide the service:</p>
          <ul className="list-disc ml-6 mt-2 space-y-1">
            <li>
              <strong>Account information:</strong> Email address and username when you register.
            </li>
            <li>
              <strong>Usage data:</strong> Pages visited, search queries, and watchlist activity
              to improve recommendations.
            </li>
            <li>
              <strong>Reviews:</strong> Any reviews or ratings you submit are stored and
              displayed publicly.
            </li>
          </ul>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">2. How We Use Your Information</h2>
          <ul className="list-disc ml-6 space-y-1">
            <li>To provide price comparison and product search features.</li>
            <li>To send price drop and stock alerts you have opted into.</li>
            <li>To improve scraper accuracy and product data quality.</li>
          </ul>
          <p className="mt-2">
            We do not sell your personal information to third parties.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">3. Authentication</h2>
          <p>
            Authentication is handled by Supabase. We do not store plaintext passwords. OAuth
            sign-in (Google, etc.) delegates authentication entirely to the OAuth provider.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">4. Cookies and Local Storage</h2>
          <p>
            We use browser local storage to remember your age verification and session state.
            We do not use third-party tracking cookies or advertising networks.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">5. Data Retention</h2>
          <p>
            Your account data is retained until you request deletion. You may request deletion
            by emailing us. Reviews are anonymized rather than deleted to preserve community
            data integrity.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">6. Security</h2>
          <p>
            Data is stored in Supabase (PostgreSQL) with encryption at rest. All traffic is
            encrypted via HTTPS. We do not log sensitive information such as passwords or
            payment data.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">7. Contact</h2>
          <p>
            Privacy questions or deletion requests:{' '}
            <a href="mailto:privacy@utahcannabiscompare.com" className="text-green-700 underline">
              privacy@utahcannabiscompare.com
            </a>
            .
          </p>
        </div>
      </section>
    </main>
  )
}

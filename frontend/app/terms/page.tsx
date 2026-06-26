export default function TermsPage() {
  return (
    <main className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>

      <p className="text-sm text-gray-500 mb-8">Last updated: April 2026</p>

      <section className="space-y-6 text-gray-700">
        <div>
          <h2 className="text-xl font-semibold mb-2">1. Informational Purpose Only</h2>
          <p>
            Utah Cannabis Compare is a price comparison and information service. We do not sell,
            distribute, or facilitate the purchase of cannabis or any controlled substance. All
            pricing and product information is sourced from licensed Utah medical cannabis
            pharmacies and is provided for informational purposes only.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">2. Medical Cannabis Disclaimer</h2>
          <p>
            This site does not provide medical advice. Cannabis products are controlled substances
            under federal law. Access to medical cannabis in Utah requires a valid Medical Cannabis
            Card issued by the Utah Department of Health and Human Services. You are solely
            responsible for complying with all applicable laws.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">3. Age Requirement</h2>
          <p>
            You must be 21 years of age or older, or a registered Utah Medical Cannabis patient,
            to use this service. By accessing this site you confirm you meet this requirement.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">4. Accuracy of Information</h2>
          <p>
            Prices and product availability change frequently. We make reasonable efforts to keep
            information current but do not guarantee accuracy. Always verify pricing and
            availability directly with the dispensary before visiting.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">5. Limitation of Liability</h2>
          <p>
            Utah Cannabis Compare is provided &ldquo;as is&rdquo; without warranties of any kind.
            We are not liable for any damages arising from your use of or reliance on information
            provided on this site.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">6. Changes to Terms</h2>
          <p>
            We may update these terms at any time. Continued use of the site after changes
            constitutes acceptance of the new terms.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">7. Contact</h2>
          <p>
            Questions about these terms? Contact us at{' '}
            <a href="mailto:legal@utahcannabiscompare.com" className="text-green-700 underline">
              legal@utahcannabiscompare.com
            </a>
            .
          </p>
        </div>
      </section>
    </main>
  )
}

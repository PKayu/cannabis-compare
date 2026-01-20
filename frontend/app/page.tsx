export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-cannabis-50 to-cannabis-100">
      {/* Compliance Banner */}
      <div className="compliance-banner max-w-7xl mx-auto">
        <p className="text-sm font-semibold">
          ⚠️ Compliance Notice: This website is for informational purposes only.
          It does not sell, advertise, or promote controlled substances.
          All information is provided for educational purposes in compliance with Utah law.
        </p>
      </div>

      {/* Header */}
      <header className="border-b border-cannabis-200 bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-4xl font-bold text-cannabis-700">
            Utah Cannabis Aggregator
          </h1>
          <p className="text-gray-600 mt-2">
            Find the best prices and read community reviews for cannabis products across Utah dispensaries
          </p>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {/* Feature 1: Price Comparison */}
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="text-4xl mb-4">💰</div>
            <h2 className="text-2xl font-bold text-cannabis-700 mb-3">
              Compare Prices
            </h2>
            <p className="text-gray-700">
              Find the best deals on cannabis products across all Utah dispensaries.
              See current pricing and stock status in real-time.
            </p>
          </div>

          {/* Feature 2: Community Reviews */}
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="text-4xl mb-4">⭐</div>
            <h2 className="text-2xl font-bold text-cannabis-700 mb-3">
              Read Reviews
            </h2>
            <p className="text-gray-700">
              Access community-driven reviews for strains and brands.
              Filter by effects, taste, and value ratings.
            </p>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex gap-4 justify-center flex-wrap">
          <button className="bg-cannabis-600 hover:bg-cannabis-700 text-white font-bold py-3 px-8 rounded-lg transition">
            Browse Products
          </button>
          <button className="bg-white text-cannabis-600 border-2 border-cannabis-600 hover:bg-cannabis-50 font-bold py-3 px-8 rounded-lg transition">
            Learn More
          </button>
        </div>
      </section>

      {/* Coming Soon Section */}
      <section className="bg-cannabis-50 py-16 mt-16">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-cannabis-700 mb-8">
            🚀 Coming Soon
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-bold text-lg mb-2">Phase 1: Data Aggregation</h3>
              <p className="text-gray-600 text-sm">
                Scraping real-time pricing from major Utah dispensaries
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-bold text-lg mb-2">Phase 2: Frontend MVP</h3>
              <p className="text-gray-600 text-sm">
                Browse products, compare prices, and search by filters
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-bold text-lg mb-2">Phase 3: Community Reviews</h3>
              <p className="text-gray-600 text-sm">
                User accounts, reviews, ratings, and upvoting system
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-cannabis-900 text-cannabis-50 py-12 mt-16">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="mb-2">Utah Cannabis Aggregator v0.1.0</p>
          <p className="text-cannabis-200 text-sm">
            For informational purposes only. Not affiliated with any dispensary.
          </p>
        </div>
      </footer>
    </main>
  )
}

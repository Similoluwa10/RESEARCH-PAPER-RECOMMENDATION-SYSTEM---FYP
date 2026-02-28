export default function RecommendationsPage() {
  return (
    <div>
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-xl font-semibold text-gray-900">
            Paper Recommendations
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            Get personalized research paper recommendations based on semantic similarity.
          </p>
        </div>
      </div>

      {/* Recommendation input placeholder */}
      <div className="mt-8 rounded-lg bg-white p-6 shadow">
        <h2 className="text-lg font-medium text-gray-900">
          Describe your research interest
        </h2>
        <div className="mt-4">
          <textarea
            rows={4}
            placeholder="Enter a description of your research topic or paste an abstract..."
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          />
        </div>
        <div className="mt-4">
          <button className="rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-500">
            Get Recommendations
          </button>
        </div>
      </div>

      {/* Results placeholder */}
      <div className="mt-8">
        <p className="text-gray-500">Recommendations will appear here.</p>
      </div>
    </div>
  );
}

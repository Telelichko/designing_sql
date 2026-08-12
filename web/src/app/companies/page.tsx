import { query } from '@/lib/db';

export default async function CompaniesPage(props: {
  searchParams: Promise<{ search?: string; city?: string }>;
}) {
  const { search = '', city = '' } = await props.searchParams;

  // Parameters for substitution (use null if the string is empty)
  const searchParam = search || null;
  const cityParam = city || null;

  // 1. Query to fetch data (limited to 100)
  const dataRes = await query(
    `
    SELECT 
      id, 
      name, 
      category, 
      city, 
      address, 
      rating, 
      reviews_count, 
      site, 
      phone, 
      email
    FROM companies
    WHERE ($1::text IS NULL OR name ILIKE '%' || $1 || '%')
      AND ($2::text IS NULL OR city ILIKE '%' || $2 || '%')
    ORDER BY rating DESC NULLS LAST
    LIMIT 100
    `,
    [searchParam, cityParam]
  );

  const companies = dataRes.rows;

  // 2. Query to count total records (without LIMIT)
  const countRes = await query(
    `
    SELECT COUNT(*) as total
    FROM companies
    WHERE ($1::text IS NULL OR name ILIKE '%' || $1 || '%')
      AND ($2::text IS NULL OR city ILIKE '%' || $2 || '%')
    `,
    [searchParam, cityParam]
  );

  const totalCount = parseInt(countRes.rows[0]?.total || '0', 10);

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Companies List</h1>
      
      {/* Search and filter form */}
      <form className="flex flex-wrap gap-4 mb-8" method="GET" action="/companies">
        <input
          type="text"
          name="search"
          placeholder="Search by name..."
          defaultValue={search}
          className="border border-gray-300 rounded-lg px-4 py-2 w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          name="city"
          placeholder="Filter by city..."
          defaultValue={city}
          className="border border-gray-300 rounded-lg px-4 py-2 w-full sm:w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button 
          type="submit" 
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
        >
          Search
        </button>
        {(search || city) && (
          <a 
            href="/companies" 
            className="text-gray-600 hover:text-gray-900 px-4 py-2 underline"
          >
            Reset
          </a>
        )}
      </form>

      {/* Data table */}
      <div className="overflow-x-auto bg-white rounded-lg shadow border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">City</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rating</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reviews</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Website</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {companies.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  No companies found. Try changing your search parameters.
                </td>
              </tr>
            ) : (
              companies.map((company) => {
                // Ensure the link has a valid format (add https:// if missing)
                const safeSite = company.site && !company.site.startsWith('http') 
                  ? `https://${company.site}` 
                  : company.site;

                return (
                  <tr key={company.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{company.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600">{company.category || '—'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600">{company.city || '—'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      {company.rating ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {company.rating}
                        </span>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600">{company.reviews_count ?? 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {safeSite ? (
                        <a 
                          href={safeSite} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-blue-600 hover:text-blue-800 hover:underline truncate block max-w-[150px]"
                          title={company.site}
                        >
                          Website
                        </a>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600 text-sm">{company.email || '—'}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
      
      {/* Additional information at the bottom (for context) */}
      <p className="mt-4 text-sm text-gray-500">
        {totalCount > 100 ? `Showing 100 out of ${totalCount} records.` : `Total ${totalCount} records.`}
      </p>
    </div>
  );
}
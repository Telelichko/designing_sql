import { query } from '@/lib/db';

export default async function CompaniesPage(props: {
  searchParams: Promise<{ search?: string; city?: string }>;
}) {
  // В Next.js 15+ searchParams является Promise
  const { search = '', city = '' } = await props.searchParams;

  const res = await query(
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
    [search || null, city || null]
  );

  const companies = res.rows;

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Список компаний</h1>
      
      {/* Форма поиска и фильтрации */}
      <form className="flex flex-wrap gap-4 mb-8" method="GET" action="/companies">
        <input
          type="text"
          name="search"
          placeholder="Поиск по названию..."
          defaultValue={search}
          className="border border-gray-300 rounded-lg px-4 py-2 w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          name="city"
          placeholder="Фильтр по городу..."
          defaultValue={city}
          className="border border-gray-300 rounded-lg px-4 py-2 w-full sm:w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button 
          type="submit" 
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
        >
          Найти
        </button>
        {(search || city) && (
          <a 
            href="/companies" 
            className="text-gray-600 hover:text-gray-900 px-4 py-2 underline"
          >
            Сбросить
          </a>
        )}
      </form>

      {/* Таблица данных */}
      <div className="overflow-x-auto bg-white rounded-lg shadow border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Название</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Категория</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Город</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Рейтинг</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Отзывы</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Сайт</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {companies.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  Компании не найдены. Попробуйте изменить параметры поиска.
                </td>
              </tr>
            ) : (
              companies.map((company) => {
                // Гарантируем, что ссылка начинается с http:// или https://
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
                          Сайт
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
      
      <p className="mt-4 text-sm text-gray-500">
        Показано до 100 записей.
      </p>
    </div>
  );
}
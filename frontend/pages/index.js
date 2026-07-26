import { useState, useEffect } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function formatPrice(price, currency) {
  const sym = { EUR: '\u20AC', GBP: '\u00A3', USD: '$' }
  return `${sym[currency] || currency} ${Number(price).toFixed(2)}`
}

export default function Dashboard() {
  const [flights, setFlights] = useState([])
  const [stats, setStats] = useState(null)
  const [sources, setSources] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searching, setSearching] = useState(false)

  // Search form state
  const [origin, setOrigin] = useState('MAN')
  const [destination, setDestination] = useState('FRA')
  const [searchDate, setSearchDate] = useState('2026-08-15')
  const [cabin, setCabin] = useState('economy')

  async function loadData() {
    try {
      const [fRes, sRes, srcRes] = await Promise.all([
        fetch(`${API_BASE}/api/flights`),
        fetch(`${API_BASE}/api/stats`),
        fetch(`${API_BASE}/api/sources`),
      ])
      const fData = await fRes.json()
      const sData = await sRes.json()
      const srcData = await srcRes.json()
      setFlights(fData.flights || [])
      setStats(sData)
      setSources(srcData.sources || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  async function handleSearch(e) {
    e.preventDefault()
    setSearching(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, destination, date: searchDate, cabin_class: cabin }),
      })
      const data = await res.json()
      if (data.status === 'error') {
        setError(data.message)
      } else {
        // Reload full data after search completes
        await loadData()
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setSearching(false)
    }
  }

  const filtered = filter === 'all'
    ? flights
    : flights.filter(f => f.source_name === filter)

  if (loading) return (
    <div style={styles.container}>
      <h2 style={styles.title}>Loading flight data...</h2>
    </div>
  )

  if (error && !stats) return (
    <div style={styles.container}>
      <h2 style={styles.title}>Cannot connect to API</h2>
      <p style={{ color: '#e74c3c' }}>{error}</p>
      <p>Make sure the backend is running at <code>{API_BASE}</code></p>
    </div>
  )

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Flight Price Comparison</h1>
        <p style={styles.subtitle}>
          {stats?.total_flights || 0} flights from {stats?.active_sources || 0} sources
          {stats?.last_updated ? ` \u00B7 Updated ${stats.last_updated}` : ''}
        </p>
      </header>

      {/* Search Form */}
      <form onSubmit={handleSearch} style={styles.searchForm}>
        <input style={styles.input} type="text" value={origin} onChange={e => setOrigin(e.target.value.toUpperCase())} placeholder="Origin" maxLength={3} />
        <input style={styles.input} type="text" value={destination} onChange={e => setDestination(e.target.value.toUpperCase())} placeholder="Dest" maxLength={3} />
        <input style={styles.input} type="date" value={searchDate} onChange={e => setSearchDate(e.target.value)} />
        <select style={styles.input} value={cabin} onChange={e => setCabin(e.target.value)}>
          <option value="economy">Economy</option>
          <option value="premium_economy">Premium Economy</option>
          <option value="business">Business</option>
          <option value="first">First</option>
        </select>
        <button type="submit" style={{ ...styles.searchBtn, opacity: searching ? 0.7 : 1 }} disabled={searching}>
          {searching ? 'Searching...' : 'Search Flights'}
        </button>
      </form>
      {error && <p style={{ color: '#e74c3c', textAlign: 'center', margin: '10px 0' }}>{error}</p>}

      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <span style={styles.statValue}>{stats?.total_flights || 0}</span>
          <span style={styles.statLabel}>Total Flights</span>
        </div>
        <div style={styles.statCard}>
          <span style={styles.statValue}>{stats?.active_sources || 0}</span>
          <span style={styles.statLabel}>Sources</span>
        </div>
        <div style={{ ...styles.statCard, border: '2px solid #27ae60' }}>
          <span style={{ ...styles.statValue, color: '#27ae60' }}>
            {stats?.cheapest ? formatPrice(stats.cheapest.price, stats.cheapest.currency) : '-'}
          </span>
          <span style={styles.statLabel}>
            Cheapest {stats?.cheapest?.airline || ''}
          </span>
        </div>
        <div style={styles.statCard}>
          <span style={styles.statValue}>
            {stats?.average_price ? formatPrice(stats.average_price, stats.currency) : '-'}
          </span>
          <span style={styles.statLabel}>Average Price</span>
        </div>
      </div>

      {/* Source Filter */}
      <div style={styles.filterBar}>
        <button
          onClick={() => setFilter('all')}
          style={{ ...styles.filterBtn, ...(filter === 'all' ? styles.filterActive : {}) }}
        >
          All Sources ({flights.length})
        </button>
        {sources.map(s => (
          <button
            key={s.name}
            onClick={() => setFilter(s.name)}
            style={{ ...styles.filterBtn, ...(filter === s.name ? styles.filterActive : {}) }}
          >
            {s.name} ({s.flight_count})
          </button>
        ))}
      </div>

      {/* Flight Table */}
      {filtered.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#888', padding: 40 }}>No flights found.</p>
      ) : (
        <div style={styles.tableWrap}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>#</th>
                <th style={styles.th}>Source</th>
                <th style={styles.th}>Airline</th>
                <th style={styles.th}>Flight</th>
                <th style={styles.th}>Departure</th>
                <th style={styles.th}>Arrival</th>
                <th style={styles.th}>Stops</th>
                <th style={styles.th}>Price</th>
                <th style={styles.th}>Converted</th>
                <th style={styles.th}>Link</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((f, i) => (
                <tr key={i} style={f.is_cheapest ? styles.cheapestRow : {}}>
                  <td style={styles.td}>{i + 1}</td>
                  <td style={styles.td}>{f.source_name}</td>
                  <td style={styles.td}>{f.airline}</td>
                  <td style={styles.td}>{f.flight_number}</td>
                  <td style={styles.td}>{f.departure_time ? `${f.departure_time} ${f.departure_tz_abbr || ''}` : '-'}</td>
                  <td style={styles.td}>{f.arrival_time ? `${f.arrival_time} ${f.arrival_tz_abbr || ''}` : '-'}</td>
                  <td style={styles.td}>{f.stops}</td>
                  <td style={styles.td}>
                    {formatPrice(f.original_price, f.original_currency)}
                  </td>
                  <td style={{ ...styles.td, fontWeight: f.is_cheapest ? 700 : 400 }}>
                    {formatPrice(f.converted_price_base, f.base_currency)}
                    {f.is_cheapest && <span style={styles.badge}>CHEAPEST</span>}
                  </td>
                  <td style={styles.td}>
                    {f.ticket_link ? (
                      <a href={f.ticket_link} target="_blank" rel="noreferrer" style={styles.link}>
                        Book
                      </a>
                    ) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <footer style={styles.footer}>
        <a href={`${API_BASE}/api/stats`} target="_blank" rel="noreferrer">API Stats</a>
        {' \u00B7 '}
        <a href={`${API_BASE}/api/sources`} target="_blank" rel="noreferrer">API Sources</a>
        {' \u00B7 '}
        <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">API Docs</a>
      </footer>
    </div>
  )
}

const styles = {
  container: { maxWidth: 1200, margin: '0 auto', padding: '20px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
  header: { textAlign: 'center', marginBottom: 20 },
  title: { fontSize: 28, fontWeight: 700, margin: 0 },
  subtitle: { color: '#666', fontSize: 14, margin: '5px 0 0' },
  searchForm: { display: 'flex', gap: 10, justifyContent: 'center', marginBottom: 20, flexWrap: 'wrap' },
  input: { padding: '8px 12px', borderRadius: 6, border: '1px solid #ddd', fontSize: 14, fontFamily: 'inherit' },
  searchBtn: { padding: '8px 20px', borderRadius: 6, border: 'none', background: '#3498db', color: '#fff', fontSize: 14, cursor: 'pointer', fontWeight: 600 },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 15, marginBottom: 25 },
  statCard: { background: '#fff', border: '1px solid #e0e0e0', borderRadius: 10, padding: '20px', textAlign: 'center' },
  statValue: { fontSize: 24, fontWeight: 700, display: 'block', color: '#2c3e50' },
  statLabel: { fontSize: 12, color: '#888', marginTop: 5 },
  filterBar: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 },
  filterBtn: { padding: '6px 14px', borderRadius: 20, border: '1px solid #ddd', background: '#fff', cursor: 'pointer', fontSize: 13 },
  filterActive: { background: '#3498db', color: '#fff', borderColor: '#3498db' },
  tableWrap: { overflowX: 'auto', background: '#fff', borderRadius: 10, border: '1px solid #e0e0e0' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { padding: '12px 10px', textAlign: 'left', borderBottom: '2px solid #eee', background: '#fafafa', fontWeight: 600, whiteSpace: 'nowrap' },
  td: { padding: '10px', borderBottom: '1px solid #f0f0f0', whiteSpace: 'nowrap' },
  cheapestRow: { background: '#f0fff4' },
  badge: { display: 'inline-block', background: '#27ae60', color: '#fff', fontSize: 10, fontWeight: 700, padding: '2px 6px', borderRadius: 4, marginLeft: 6 },
  link: { color: '#3498db', textDecoration: 'none', fontWeight: 600 },
  footer: { textAlign: 'center', marginTop: 30, padding: 20, color: '#888', fontSize: 13 },
}

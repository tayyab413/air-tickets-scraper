import { useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function formatPrice(price, currency) {
  const sym = { EUR: '\u20AC', GBP: '\u00A3', USD: '$' }
  return `${sym[currency] || currency}${Number(price).toFixed(2)}`
}

export default function Dashboard() {
  const [flights, setFlights] = useState([])
  const [stats, setStats] = useState(null)
  const [sources, setSources] = useState([])
  const [filter, setFilter] = useState('all')
  const [error, setError] = useState(null)
  const [searching, setSearching] = useState(false)

  const [origin, setOrigin] = useState('MAN')
  const [destination, setDestination] = useState('FRA')
  const [searchDate, setSearchDate] = useState('2026-08-15')
  const [cabin, setCabin] = useState('economy')
  // Start empty — no initial data load

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
    }
  }

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

  if (error && !stats) return (
    <div style={s.container}>
      <div style={s.header}>
        <h1 style={s.title}>Cannot Connect</h1>
        <p style={{ color: '#ef4444' }}>{error}</p>
        <p style={s.subtitle}>Make sure the backend is running at <code>{API_BASE}</code></p>
      </div>
    </div>
  )

  return (
    <div style={s.container}>
      <div style={s.header}>
        <h1 style={s.title}>Flight Price Comparison</h1>
        <p style={s.subtitle}>
          {stats?.total_flights || 0} flights &middot; {stats?.active_sources || 0} sources
          {stats?.last_updated ? ` \u00B7 Updated ${stats.last_updated} ${stats.server_tz || ''}` : ''}
        </p>
      </div>

      <form onSubmit={handleSearch} style={s.searchForm}>
        <input style={s.input} type="text" value={origin} onChange={e => setOrigin(e.target.value.toUpperCase())} placeholder="Origin" maxLength={3} />
        <input style={s.input} type="text" value={destination} onChange={e => setDestination(e.target.value.toUpperCase())} placeholder="Dest" maxLength={3} />
        <input style={s.input} type="date" value={searchDate} onChange={e => setSearchDate(e.target.value)} />
        <select style={s.input} value={cabin} onChange={e => setCabin(e.target.value)}>
          <option value="economy">Economy</option>
          <option value="premium_economy">Premium Economy</option>
          <option value="business">Business</option>
          <option value="first">First</option>
        </select>
        <button type="submit" style={{ ...s.searchBtn, opacity: searching ? 0.7 : 1 }} disabled={searching}>
          {searching ? 'Searching...' : 'Search Flights'}
        </button>
      </form>
      {error && <p style={{ color: '#ef4444', textAlign: 'center', margin: '0 0 16px', fontSize: 14 }}>{error}</p>}

      <div style={s.statsGrid}>
        <div style={s.statCard}>
          <span style={{ ...s.statValue, color: '#2563eb' }}>{stats?.total_flights || 0}</span>
          <span style={s.statLabel}>Total Flights</span>
        </div>
        <div style={s.statCard}>
          <span style={{ ...s.statValue, color: '#7c3aed' }}>{stats?.active_sources || 0}</span>
          <span style={s.statLabel}>Sources</span>
        </div>
        <div style={{ ...s.statCard, border: '2px solid #059669' }}>
          <span style={{ ...s.statValue, color: '#059669' }}>
            {stats?.cheapest ? formatPrice(stats.cheapest.price, stats.cheapest.currency) : '-'}
          </span>
          <span style={s.statLabel}>
            Cheapest {stats?.cheapest?.airline || ''}
          </span>
        </div>
        <div style={s.statCard}>
          <span style={{ ...s.statValue, color: '#d97706' }}>
            {stats?.average_price ? formatPrice(stats.average_price, stats.currency) : '-'}
          </span>
          <span style={s.statLabel}>Average Price</span>
        </div>
      </div>

      <div style={s.filterBar}>
        <button onClick={() => setFilter('all')} style={{ ...s.filterBtn, ...(filter === 'all' ? s.filterActive : {}) }}>
          All Sources ({flights.length})
        </button>
        {sources.map(s => (
          <button key={s.name} onClick={() => setFilter(s.name)} style={{ ...s.filterBtn, ...(filter === s.name ? s.filterActive : {}) }}>
            {s.name} ({s.flight_count})
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div style={s.empty}>
          <p style={{ fontSize: 18, fontWeight: 600, margin: '0 0 4px' }}>No flights found</p>
          <p style={{ margin: 0, color: '#888' }}>Try a different route, date, or cabin class</p>
        </div>
      ) : (
        <div style={s.tableWrap}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>#</th>
                <th style={s.th}>Source</th>
                <th style={s.th}>Airline</th>
                <th style={s.th}>Flight</th>
                <th style={s.th}>Departure</th>
                <th style={s.th}>Arrival</th>
                <th style={s.th}>Stops</th>
                <th style={s.th}>Cabin</th>
                <th style={s.th}>Price</th>
                <th style={s.th}>EUR</th>
                <th style={s.th}></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((f, i) => (
                <tr key={i} style={{ ...s.tr, ...(f.is_cheapest ? s.cheapestRow : {}), ...(i % 2 === 0 ? {} : s.evenRow) }}>
                  <td style={s.td}>{i + 1}</td>
                  <td style={s.td}><span style={sourceBadge(f.source_name)}>{f.source_name}</span></td>
                  <td style={s.td}>{f.airline}</td>
                  <td style={{ ...s.td, fontFamily: 'monospace' }}>{f.flight_number || '-'}</td>
                  <td style={s.td}>{f.departure_time ? `${f.departure_time} ${f.departure_tz_abbr || ''}` : '-'}</td>
                  <td style={s.td}>{f.arrival_time ? `${f.arrival_time} ${f.arrival_tz_abbr || ''}` : '-'}</td>
                  <td style={s.td}>
                    <span style={stopsBadge(f.stops)}>
                      {f.stops === 0 ? 'Direct' : `${f.stops} stop${f.stops > 1 ? 's' : ''}`}
                    </span>
                  </td>
                  <td style={s.td}>{f.cabin_class_original || f.cabin_class}</td>
                  <td style={s.td}>{formatPrice(f.original_price, f.original_currency)}</td>
                  <td style={{ ...s.td, fontWeight: f.is_cheapest ? 700 : 400 }}>
                    {formatPrice(f.converted_price_base, f.base_currency)}
                    {f.is_cheapest && <span style={s.badge}>CHEAPEST</span>}
                  </td>
                  <td style={s.td}>
                    {f.ticket_link ? (
                      <a href={f.ticket_link} target="_blank" rel="noreferrer" style={s.link}>Book &rarr;</a>
                    ) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={s.footer}>
        <a href={`${API_BASE}/api/stats`} target="_blank" rel="noreferrer">API Stats</a>
        {' \u00B7 '}
        <a href={`${API_BASE}/api/sources`} target="_blank" rel="noreferrer">API Sources</a>
        {' \u00B7 '}
        <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">API Docs</a>
      </div>

    </div>
  )
}

function sourceBadge(name) {
  const colors = {
    'Ignav API': { bg: '#dbeafe', color: '#1d4ed8' },
    'Google Flights': { bg: '#d1fae5', color: '#047857' },
    'WhentoFly': { bg: '#fef3c7', color: '#b45309' },
    'OctoTrip': { bg: '#ede9fe', color: '#6d28d9' },
    'Kayak': { bg: '#fce7f3', color: '#be185d' },
  }
  const c = colors[name] || { bg: '#f3f4f6', color: '#374151' }
  return { display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: c.bg, color: c.color }
}

function stopsBadge(stops) {
  const color = stops === 0 ? '#059669' : stops === 1 ? '#d97706' : '#dc2626'
  const bg = stops === 0 ? '#ecfdf5' : stops === 1 ? '#fffbeb' : '#fef2f2'
  return { display: 'inline-block', padding: '2px 6px', borderRadius: 4, fontSize: 11, fontWeight: 600, color, background: bg }
}

const s = {
  container: {
    maxWidth: 1280, margin: '0 auto', padding: '24px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
    background: '#f8fafc', minHeight: '100vh',
  },
  header: {
    textAlign: 'center', marginBottom: 24,
    background: 'linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)',
    margin: '-24px -24px 24px', padding: '32px 24px',
    color: '#fff',
  },
  title: { fontSize: 28, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' },
  subtitle: { color: 'rgba(255,255,255,0.8)', fontSize: 14, margin: '6px 0 0' },
  searchForm: {
    display: 'flex', gap: 10, justifyContent: 'center', marginBottom: 24, flexWrap: 'wrap',
  },
  input: {
    padding: '10px 14px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14,
    fontFamily: 'inherit', background: '#fff', outline: 'none', transition: 'border-color 0.15s',
  },
  searchBtn: {
    padding: '10px 24px', borderRadius: 8, border: 'none', background: '#2563eb',
    color: '#fff', fontSize: 14, cursor: 'pointer', fontWeight: 600,
    transition: 'background 0.15s',
  },
  statsGrid: {
    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 16, marginBottom: 24,
  },
  statCard: {
    background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12,
    padding: '20px 16px', textAlign: 'center', boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  statValue: { fontSize: 26, fontWeight: 800, display: 'block' },
  statLabel: { fontSize: 12, color: '#6b7280', marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.5px' },
  filterBar: {
    display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20,
    justifyContent: 'center',
  },
  filterBtn: {
    padding: '6px 16px', borderRadius: 20, border: '1px solid #d1d5db',
    background: '#fff', cursor: 'pointer', fontSize: 13, fontWeight: 500,
    transition: 'all 0.15s',
  },
  filterActive: { background: '#2563eb', color: '#fff', borderColor: '#2563eb' },
  empty: {
    textAlign: 'center', padding: '60px 20px', background: '#fff',
    borderRadius: 12, border: '1px solid #e5e7eb',
  },
  tableWrap: {
    overflowX: 'auto', background: '#fff', borderRadius: 12,
    border: '1px solid #e5e7eb', boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: {
    padding: '12px 10px', textAlign: 'left', borderBottom: '2px solid #e5e7eb',
    background: '#f9fafb', fontWeight: 600, whiteSpace: 'nowrap',
    color: '#374151', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px',
  },
  tr: { transition: 'background 0.1s' },
  evenRow: { background: '#fafafa' },
  td: { padding: '10px', borderBottom: '1px solid #f3f4f6', whiteSpace: 'nowrap' },
  cheapestRow: { background: '#f0fdf4' },
  badge: {
    display: 'inline-block', background: '#059669', color: '#fff',
    fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
    marginLeft: 6, letterSpacing: '0.3px',
  },
  link: {
    color: '#2563eb', textDecoration: 'none', fontWeight: 600, fontSize: 12,
  },
  footer: {
    textAlign: 'center', marginTop: 32, padding: 20, color: '#9ca3af', fontSize: 13,
  },
}

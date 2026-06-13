/**
 * data.js
 * Simulated data layer — mirrors what the Flask API returns.
 * When running with the backend, replace DATA.fetch() calls with
 * real fetch('/api/...') calls in main.js.
 *
 * All numbers are realistic approximations of NYC Yellow Taxi Jan 2024.
 */

const DATA = (() => {

  // ── Zone lookup (real data from taxi_zone_lookup.csv) ──────────────────
  const ZONES = [
    {zone_id:1,  zone_name:"Newark Airport",               borough:"EWR",          service_zone:"EWR",         total_trips:420,  avg_fare:52.10},
    {zone_id:4,  zone_name:"Alphabet City",                borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:3820, avg_fare:14.80},
    {zone_id:7,  zone_name:"Astoria",                      borough:"Queens",       service_zone:"Boro Zone",   total_trips:1940, avg_fare:22.40},
    {zone_id:12, zone_name:"Battery Park",                 borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:2910, avg_fare:17.20},
    {zone_id:13, zone_name:"Battery Park City",            borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:2640, avg_fare:16.90},
    {zone_id:24, zone_name:"Bloomingdale",                 borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:1820, avg_fare:15.40},
    {zone_id:33, zone_name:"Brooklyn Heights",             borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:980,  avg_fare:19.20},
    {zone_id:36, zone_name:"Bushwick North",               borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:640,  avg_fare:18.60},
    {zone_id:40, zone_name:"Carroll Gardens",              borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:720,  avg_fare:20.10},
    {zone_id:41, zone_name:"Central Harlem",               borough:"Manhattan",    service_zone:"Boro Zone",   total_trips:2100, avg_fare:13.80},
    {zone_id:43, zone_name:"Central Park",                 borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4100, avg_fare:16.30},
    {zone_id:45, zone_name:"Chinatown",                    borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:2750, avg_fare:13.60},
    {zone_id:48, zone_name:"Clinton East",                 borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:3410, avg_fare:14.90},
    {zone_id:49, zone_name:"Clinton Hill",                 borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:810,  avg_fare:21.40},
    {zone_id:50, zone_name:"Clinton West",                 borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:3150, avg_fare:15.10},
    {zone_id:65, zone_name:"Downtown Brooklyn/MetroTech",  borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:1240, avg_fare:20.80},
    {zone_id:68, zone_name:"East Chelsea",                 borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4220, avg_fare:15.60},
    {zone_id:69, zone_name:"East Concourse/Concourse Vill",borough:"Bronx",        service_zone:"Boro Zone",   total_trips:480,  avg_fare:16.40},
    {zone_id:74, zone_name:"East Harlem North",            borough:"Manhattan",    service_zone:"Boro Zone",   total_trips:1680, avg_fare:13.20},
    {zone_id:79, zone_name:"East Village",                 borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5140, avg_fare:13.90},
    {zone_id:80, zone_name:"East Williamsburg",            borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:920,  avg_fare:19.80},
    {zone_id:87, zone_name:"Financial District North",     borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5800, avg_fare:16.10},
    {zone_id:88, zone_name:"Financial District South",     borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5200, avg_fare:16.40},
    {zone_id:90, zone_name:"Flatiron",                     borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:6100, avg_fare:15.80},
    {zone_id:92, zone_name:"Flushing",                     borough:"Queens",       service_zone:"Boro Zone",   total_trips:1420, avg_fare:24.60},
    {zone_id:97, zone_name:"Fort Greene",                  borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:860,  avg_fare:20.60},
    {zone_id:100,zone_name:"Garment District",             borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:7200, avg_fare:15.20},
    {zone_id:106,zone_name:"Gowanus",                      borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:690,  avg_fare:20.30},
    {zone_id:107,zone_name:"Gramercy",                     borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5400, avg_fare:15.60},
    {zone_id:112,zone_name:"Greenpoint",                   borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:1040, avg_fare:21.60},
    {zone_id:113,zone_name:"Greenwich Village North",      borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4800, avg_fare:14.70},
    {zone_id:114,zone_name:"Greenwich Village South",      borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4200, avg_fare:14.50},
    {zone_id:119,zone_name:"Highbridge",                   borough:"Bronx",        service_zone:"Boro Zone",   total_trips:310,  avg_fare:15.80},
    {zone_id:125,zone_name:"Hudson Sq",                    borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:3600, avg_fare:15.00},
    {zone_id:129,zone_name:"Jackson Heights",              borough:"Queens",       service_zone:"Boro Zone",   total_trips:820,  avg_fare:19.40},
    {zone_id:130,zone_name:"Jamaica",                      borough:"Queens",       service_zone:"Boro Zone",   total_trips:960,  avg_fare:22.80},
    {zone_id:132,zone_name:"JFK Airport",                  borough:"Queens",       service_zone:"Airports",    total_trips:8400, avg_fare:52.20},
    {zone_id:137,zone_name:"Kips Bay",                     borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:3900, avg_fare:15.40},
    {zone_id:138,zone_name:"LaGuardia Airport",            borough:"Queens",       service_zone:"Airports",    total_trips:6200, avg_fare:36.80},
    {zone_id:140,zone_name:"Lenox Hill East",              borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5600, avg_fare:16.20},
    {zone_id:141,zone_name:"Lenox Hill West",              borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5100, avg_fare:16.00},
    {zone_id:142,zone_name:"Lincoln Square East",          borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4700, avg_fare:16.40},
    {zone_id:143,zone_name:"Lincoln Square West",          borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4200, avg_fare:16.20},
    {zone_id:144,zone_name:"Little Italy/NoLiTa",          borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:3100, avg_fare:14.20},
    {zone_id:145,zone_name:"Long Island City/Hunters Pt",  borough:"Queens",       service_zone:"Boro Zone",   total_trips:1680, avg_fare:20.60},
    {zone_id:146,zone_name:"Long Island City/Queens Plaza",borough:"Queens",       service_zone:"Boro Zone",   total_trips:1540, avg_fare:19.80},
    {zone_id:148,zone_name:"Lower East Side",              borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4100, avg_fare:13.80},
    {zone_id:151,zone_name:"Manhattan Valley",             borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:3200, avg_fare:15.60},
    {zone_id:158,zone_name:"Meatpacking/West Village West",borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4600, avg_fare:15.20},
    {zone_id:161,zone_name:"Midtown Center",               borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:14200,avg_fare:17.80},
    {zone_id:162,zone_name:"Midtown East",                 borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:12800,avg_fare:17.40},
    {zone_id:163,zone_name:"Midtown North",                borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:11600,avg_fare:17.20},
    {zone_id:164,zone_name:"Midtown South",                borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:10400,avg_fare:16.80},
    {zone_id:166,zone_name:"Morningside Heights",          borough:"Manhattan",    service_zone:"Boro Zone",   total_trips:1900, avg_fare:14.20},
    {zone_id:168,zone_name:"Mott Haven/Port Morris",       borough:"Bronx",        service_zone:"Boro Zone",   total_trips:540,  avg_fare:17.60},
    {zone_id:170,zone_name:"Murray Hill",                  borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:6800, avg_fare:15.80},
    {zone_id:181,zone_name:"Park Slope",                   borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:1320, avg_fare:21.80},
    {zone_id:186,zone_name:"Penn Station/Madison Sq West", borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:9200, avg_fare:16.60},
    {zone_id:189,zone_name:"Prospect Heights",             borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:740,  avg_fare:20.90},
    {zone_id:195,zone_name:"Red Hook",                     borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:620,  avg_fare:22.40},
    {zone_id:202,zone_name:"Roosevelt Island",             borough:"Manhattan",    service_zone:"Boro Zone",   total_trips:940,  avg_fare:14.60},
    {zone_id:206,zone_name:"Saint George/New Brighton",    borough:"Staten Island",service_zone:"Boro Zone",   total_trips:190,  avg_fare:18.20},
    {zone_id:209,zone_name:"Seaport",                      borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4400, avg_fare:16.80},
    {zone_id:211,zone_name:"SoHo",                         borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5600, avg_fare:15.40},
    {zone_id:221,zone_name:"Stapleton",                    borough:"Staten Island",service_zone:"Boro Zone",   total_trips:160,  avg_fare:17.80},
    {zone_id:224,zone_name:"Stuy Town/Peter Cooper Village",borough:"Manhattan",   service_zone:"Yellow Zone", total_trips:3400, avg_fare:15.20},
    {zone_id:229,zone_name:"Sutton Place/Turtle Bay North",borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4100, avg_fare:15.60},
    {zone_id:230,zone_name:"Times Sq/Theatre District",    borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:13600,avg_fare:18.20},
    {zone_id:231,zone_name:"TriBeCa/Civic Center",         borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4800, avg_fare:16.20},
    {zone_id:232,zone_name:"Two Bridges/Seward Park",      borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:2800, avg_fare:13.60},
    {zone_id:233,zone_name:"UN/Turtle Bay South",          borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:3600, avg_fare:15.80},
    {zone_id:234,zone_name:"Union Sq",                     borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:7200, avg_fare:15.00},
    {zone_id:236,zone_name:"Upper East Side North",        borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:8200, avg_fare:16.40},
    {zone_id:237,zone_name:"Upper East Side South",        borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:9400, avg_fare:16.60},
    {zone_id:238,zone_name:"Upper West Side North",        borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:7600, avg_fare:16.20},
    {zone_id:239,zone_name:"Upper West Side South",        borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:8800, avg_fare:16.40},
    {zone_id:243,zone_name:"Washington Heights North",     borough:"Manhattan",    service_zone:"Boro Zone",   total_trips:1200, avg_fare:13.40},
    {zone_id:244,zone_name:"Washington Heights South",     borough:"Manhattan",    service_zone:"Boro Zone",   total_trips:1400, avg_fare:13.60},
    {zone_id:246,zone_name:"West Chelsea/Hudson Yards",    borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5200, avg_fare:15.80},
    {zone_id:249,zone_name:"West Village",                 borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5400, avg_fare:15.00},
    {zone_id:255,zone_name:"Williamsburg (North Side)",    borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:1640, avg_fare:20.40},
    {zone_id:256,zone_name:"Williamsburg (South Side)",    borough:"Brooklyn",     service_zone:"Boro Zone",   total_trips:1480, avg_fare:20.20},
    {zone_id:261,zone_name:"World Trade Center",           borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:5800, avg_fare:17.40},
    {zone_id:262,zone_name:"Yorkville East",               borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:4200, avg_fare:15.80},
    {zone_id:263,zone_name:"Yorkville West",               borough:"Manhattan",    service_zone:"Yellow Zone", total_trips:3800, avg_fare:15.60},
  ];

  // ── Hourly baseline (avg trips/hr across Jan 2024) ──────────────────────
  const HOURLY_TRIPS  = [320,210,140,100,130,280,620,1100,1350,1200,1050,1100,1180,1120,1050,1080,1200,1420,1500,1380,1150,950,780,530];
  const HOURLY_FARES  = [28.4,31.2,33.8,35.1,32.6,27.4,19.8,16.2,15.8,16.4,17.2,17.8,18.1,17.9,17.4,17.6,18.4,19.2,19.8,19.4,18.6,18.1,20.4,24.8];
  const HOURLY_SPEEDS = [26.8,27.4,27.9,28.2,27.1,24.6,18.4,12.1,10.8,11.4,12.8,13.2,13.6,13.8,13.4,12.9,11.4,10.2,10.8,11.6,13.4,15.2,18.6,22.4];

  // ── Daily trips (Jan 1–31, 2024) ───────────────────────────────────────
  const DAILY = [
    {pickup_date:"2024-01-01",trips:71400,avg_fare:19.2},
    {pickup_date:"2024-01-02",trips:98600,avg_fare:18.1},
    {pickup_date:"2024-01-03",trips:102400,avg_fare:17.9},
    {pickup_date:"2024-01-04",trips:104200,avg_fare:18.0},
    {pickup_date:"2024-01-05",trips:106800,avg_fare:17.8},
    {pickup_date:"2024-01-06",trips:88400,avg_fare:19.4},
    {pickup_date:"2024-01-07",trips:76200,avg_fare:20.1},
    {pickup_date:"2024-01-08",trips:101800,avg_fare:18.2},
    {pickup_date:"2024-01-09",trips:105400,avg_fare:17.9},
    {pickup_date:"2024-01-10",trips:107200,avg_fare:17.8},
    {pickup_date:"2024-01-11",trips:108600,avg_fare:17.7},
    {pickup_date:"2024-01-12",trips:109400,avg_fare:17.6},
    {pickup_date:"2024-01-13",trips:91200,avg_fare:19.2},
    {pickup_date:"2024-01-14",trips:78800,avg_fare:20.4},
    {pickup_date:"2024-01-15",trips:103600,avg_fare:18.0},
    {pickup_date:"2024-01-16",trips:106200,avg_fare:17.8},
    {pickup_date:"2024-01-17",trips:108400,avg_fare:17.7},
    {pickup_date:"2024-01-18",trips:110200,avg_fare:17.5},
    {pickup_date:"2024-01-19",trips:111600,avg_fare:17.4},
    {pickup_date:"2024-01-20",trips:86400,avg_fare:19.6},
    {pickup_date:"2024-01-21",trips:74600,avg_fare:20.8},
    {pickup_date:"2024-01-22",trips:104800,avg_fare:17.9},
    {pickup_date:"2024-01-23",trips:107400,avg_fare:17.7},
    {pickup_date:"2024-01-24",trips:64200,avg_fare:22.4},  // storm
    {pickup_date:"2024-01-25",trips:58600,avg_fare:24.8},  // storm
    {pickup_date:"2024-01-26",trips:82400,avg_fare:20.2},
    {pickup_date:"2024-01-27",trips:76800,avg_fare:20.6},
    {pickup_date:"2024-01-28",trips:102400,avg_fare:18.1},
    {pickup_date:"2024-01-29",trips:105800,avg_fare:17.8},
    {pickup_date:"2024-01-30",trips:108200,avg_fare:17.6},
    {pickup_date:"2024-01-31",trips:110400,avg_fare:17.5},
  ];

  // ── Heatmap (dow × hour) ────────────────────────────────────────────────
  const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  const HEATMAP = DAYS.map((d, di) => ({
    day: d,
    hours: HOURLY_TRIPS.map((v, h) => {
      let m = 1;
      if (di >= 5) m = (h >= 10 && h <= 22) ? 1.3 : 0.65;
      if (di < 5 && (h === 8 || h === 9 || h === 17 || h === 18)) m = 1.45;
      return Math.round(v * m);
    })
  }));

  // ── Public API ──────────────────────────────────────────────────────────
  return {
    kpis() {
      return {
        total_trips: 2963400, avg_fare: 18.40, avg_distance_mi: 3.1,
        avg_duration_min: 14.2, avg_tip_pct: 18.3, avg_total_amount: 26.15,
        avg_speed_mph: 12.8, active_zones: 241
      };
    },
    dailyTrips()    { return DAILY; },
    hourlyVolume()  {
      return HOURLY_TRIPS.map((v, h) => ({
        hour: h, total_trips: v * 31,
        avg_trips_per_day: v,
        avg_fare: HOURLY_FARES[h],
        avg_speed_mph: HOURLY_SPEEDS[h],
        fare_per_minute: +(HOURLY_FARES[h] / (60 / HOURLY_SPEEDS[h] * 0.6)).toFixed(2)
      }));
    },
    boroughSummary() {
      return [
        {borough:"Manhattan",   trips:2133648, pct:72.0, avg_fare:17.80, avg_distance:2.6, total_revenue:52100000},
        {borough:"Queens",      trips:444510,  pct:15.0, avg_fare:24.60, avg_distance:5.8, total_revenue:14200000},
        {borough:"Brooklyn",    trips:266706,  pct:9.0,  avg_fare:20.40, avg_distance:3.8, total_revenue:7100000},
        {borough:"Bronx",       trips:88902,   pct:3.0,  avg_fare:16.80, avg_distance:3.2, total_revenue:2000000},
        {borough:"Staten Island",trips:29634,  pct:1.0,  avg_fare:18.20, avg_distance:4.1, total_revenue:640000},
        {borough:"EWR",         trips:12420,   pct:0.4,  avg_fare:52.10, avg_distance:14.2,total_revenue:740000},
      ];
    },
    topZones(n=10) {
      return [...ZONES].sort((a,b) => b.total_trips - a.total_trips).slice(0, n);
    },
    paymentBreakdown() {
      return [
        {payment_type:1, label:"Credit card", trips:1985478, pct:67.0, avg_fare:18.60, avg_tip_pct:23.4},
        {payment_type:2, label:"Cash",         trips:829752,  pct:28.0, avg_fare:17.80, avg_tip_pct:0.0},
        {payment_type:3, label:"No charge",    trips:88902,   pct:3.0,  avg_fare:0.00,  avg_tip_pct:0.0},
        {payment_type:4, label:"Dispute",      trips:59268,   pct:2.0,  avg_fare:14.20, avg_tip_pct:0.0},
      ];
    },
    fareDistribution() {
      return [
        {bucket:"Under $5",  pct:3},  {bucket:"$5–10",   pct:14},
        {bucket:"$10–15",    pct:22}, {bucket:"$15–20",  pct:21},
        {bucket:"$20–30",    pct:19}, {bucket:"$30–50",  pct:12},
        {bucket:"$50+",      pct:9},
      ];
    },
    fareByHour()  { return HOURLY_TRIPS.map((_,h) => ({hour:h, avg_fare:HOURLY_FARES[h], fare_per_minute:+(HOURLY_FARES[h]/14.2*0.8).toFixed(2)})); },
    distanceDist() {
      return [
        {bucket:"0–1 mi",   pct:18}, {bucket:"1–2 mi",  pct:24},
        {bucket:"2–3 mi",   pct:21}, {bucket:"3–5 mi",  pct:17},
        {bucket:"5–10 mi",  pct:12}, {bucket:"10–20 mi",pct:6},
        {bucket:"20+ mi",   pct:2},
      ];
    },
    heatmap()      { return HEATMAP; },
    rushComparison() {
      return [
        {is_rush_hour:1, trips:710016,  avg_fare:17.20, avg_speed:10.2, avg_duration_min:16.8, avg_tip_pct:19.2},
        {is_rush_hour:0, trips:2253384, avg_fare:18.80, avg_speed:13.6, avg_duration_min:13.4, avg_tip_pct:17.8},
      ];
    },
    zones(filters={}) {
      let list = [...ZONES];
      if (filters.borough) list = list.filter(z => z.borough === filters.borough);
      if (filters.service) list = list.filter(z => z.service_zone === filters.service);
      if (filters.search)  list = list.filter(z => z.zone_name.toLowerCase().includes(filters.search.toLowerCase()));
      const total = list.length;
      const page = filters.page || 1;
      const per_page = filters.per_page || 15;
      const start = (page-1)*per_page;
      return { data: list.slice(start, start+per_page), total, page, per_page };
    },
    insightAirport() {
      return [
        {service_zone:"EWR",         avg_fare:52.10, trips:12420},
        {service_zone:"Airports",    avg_fare:44.20, trips:127200},
        {service_zone:"Yellow Zone", avg_fare:17.80, trips:2216000},
        {service_zone:"Boro Zone",   avg_fare:14.20, trips:607780},
      ];
    },
    insightNight() {
      return HOURLY_TRIPS.map((_,h) => ({
        hour: h,
        avg_speed: HOURLY_SPEEDS[h],
        fare_per_min: +(HOURLY_FARES[h] / 14.2 * 0.8).toFixed(2),
        trips: HOURLY_TRIPS[h]*31
      }));
    },
    insightTips() {
      return [
        {payment_type:1, label:"Credit card", avg_tip_pct:23.4, avg_tip_amount:4.36},
        {payment_type:2, label:"Cash",         avg_tip_pct:0.0,  avg_tip_amount:0.0},
        {payment_type:3, label:"No charge",    avg_tip_pct:0.0,  avg_tip_amount:0.0},
        {payment_type:4, label:"Dispute",      avg_tip_pct:0.0,  avg_tip_amount:0.0},
      ];
    },
  };
})();

import React, { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'

import { useDemoStore } from '../store'

const chartData = {
  x: [
    'Direct',
    'Referral',
    'Organic Search',
    'Organic Social',
    'Organic Video',
    'Paid',
  ],
  y: [290, 260, 180, 140, 115, 100],
}

const TYPE_CONFIG = [
  { id: 'pie', icon: 'fa-chart-pie' },
  { id: 'bar', icon: 'fa-chart-bar' },
  { id: 'line', icon: 'fa-chart-line' },
]

const THEME_CONFIG = [
  {
    id: 'indigo',
    palette: [
      '#6366f1',
      '#4f46e5',
      '#4338ca',
      '#3730a3',
      '#312e81',
      '#e0e7ff',
      '#c7d2fe',
      '#a5b4fc',
      '#818cf8',
    ],
  },
  {
    id: 'green',
    palette: [
      '#48bb78',
      '#38a169',
      '#2f855a',
      '#276749',
      '#22543d',
      '#f0fff4',
      '#c6f6d5',
      '#9ae6b4',
      '#68d391',
    ],
  },
  {
    id: 'yellow',
    palette: [
      '#ecc94b',
      '#d69e2e',
      '#b7791f',
      '#975a16',
      '#744210',
      '#fffff0',
      '#fefcbf',
      '#faf089',
      '#f6e05e',
    ],
  },
]

const FONT_CONFIG = ['sans-serif', 'serif', 'monospace']

const AGENCY_CONFIG = [
  { id: 'squirrel', name: 'Squirrel' },
  { id: 'rabbit', name: 'Rabbit' },
  { id: 'otter', name: 'Otter' },
]

const TypeButtonGroup = ({ type, setType }) => {
  return (
    <div className='flex divide-x card card--none'>
      {TYPE_CONFIG.map((option) => (
        <button
          key={option.id}
          className={`p-2 text-lg lg:text-xl focus:outline-none h-full ${
            type === option.id
              ? 'text-white bg-indigo-600 hover:bg-indigo-700'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          onClick={() => setType(option.id)}
        >
          <i className={`fa ${option.icon}`}></i>
        </button>
      ))}
    </div>
  )
}

const ThemeButtonGroup = ({ theme, setTheme }) => {
  return (
    <div className='flex divide-x card card--none'>
      {THEME_CONFIG.map(({ id }) => (
        <button
          key={id}
          className={`p-2 focus:outline-none w-10 h-full ${
            theme === id
              ? `bg-${id}-600 hover:bg-${id}-700`
              : `bg-${id}-100 hover:bg-${id}-200`
          }`}
          onClick={() => setTheme(id)}
        ></button>
      ))}
    </div>
  )
}

const FontButtonGroup = ({ font, setFont }) => {
  return (
    <div className='flex divide-x card card--none'>
      {FONT_CONFIG.map((id) => (
        <button
          key={id}
          style={{ fontFamily: id }}
          className={`p-2 text-lg lg:text-xl focus:outline-none w-10 h-full ${
            font === id
              ? 'text-white bg-indigo-600 hover:bg-indigo-700'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          onClick={() => setFont(id)}
        >
          T
        </button>
      ))}
    </div>
  )
}

const AgencyButtonGroup = ({ agency, setAgency }) => {
  return (
    <div className='flex divide-x card card--none'>
      {AGENCY_CONFIG.map(({ id }) => (
        <button
          key={id}
          className={`p-2 text-lg lg:text-xl focus:outline-none w-10 h-full ${
            agency === id
              ? 'text-white bg-indigo-600 hover:bg-indigo-700'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          onClick={() => setAgency(id)}
        >
          <i className={`fa fa-${id}`}></i>
        </button>
      ))}
    </div>
  )
}

const DashboardDemo = () => {
  const [type, setType] = useState('pie')
  const [theme, setTheme] = useState('indigo')
  const [font, setFont] = useState('sans-serif')
  const [agency, setAgency] = useState('squirrel')
  const [data, setData] = useState(chartData)

  const { integrations, node } = useDemoStore()[0]

  const palette = THEME_CONFIG.find((item) => item.id === theme)?.palette

  const plotlyData = {
    ...data,
    labels: data.x,
    values: data.y,
    type,
    marker: {
      colors: palette,
      color: palette[0],
      line: { color: palette },
    },
  }

  const plotlyLayout = {
    showlegend: false,
    font: { family: font },
    height: 250,
    margin: { l: 40, r: 40, t: 40, b: 60 },
  }

  const plotlyConfig = { displayModeBar: false, responsive: true }

  useEffect(() => {
    setData({
      x: chartData.x,
      y: chartData.y.map((p) => p + Math.floor(Math.random() * 240) - 120),
    })
  }, [JSON.stringify({ integrations, node })])

  return (
    <div className='p-4 lg:p-0 flex flex-col gap-4 h-full'>
      <div className='card card--none flex-grow flex flex-col bg-gray-10 relative'>
        <div className='w-full bg-gray-10 p-1'>
          <div
            className='px-2 py-1 border border-gray rounded-lg bg-white focus:outline-none'
            contentEditable
            suppressContentEditableWarning
          >
            <i className='fa fa-search text-gray mr-1'></i>
            <span className='text-black-20'>https://</span>dashboard.{agency}
            .com
          </div>
        </div>
        <div className='w-full bg-gray-10 flex-none flex items-center gap-2 p-2 border-b border-gray'>
          <div
            className={`p-1 flex items-center justify-center bg-${theme}-100 rounded-lg border border-${theme}-400 p-2`}
          >
            <i className={`fad fa-fw fa-${agency} fa-2x text-${theme}-600`}></i>
          </div>
          <div>
            <h2 className='text-lg lg:text-xl' style={{ fontFamily: font }}>
              Marketing Performance Report
            </h2>
            <p>{AGENCY_CONFIG.find((item) => item.id === agency)?.name} Inc.</p>
          </div>
        </div>
        <div className='flex flex-col'>
          <Plot
            data={[plotlyData]}
            layout={plotlyLayout}
            config={plotlyConfig}
          />
        </div>
        <p className='absolute bottom-0 right-0 text-gray-600 text-sm inline-flex items-center gap-1 bg-gray-10 p-1 m-2 rounded border border-gray'>
          Data sources
          {integrations.map((integration) => (
            <img
              key={integration.name}
              className='w-4 h-4 rounded-sm'
              src={`/static/images/integrations/fivetran/${integration.icon_path}`}
              alt={integration.name}
            />
          ))}
          {node && (
            <>
              +<i className={`fa ${node.icon}`}></i>
            </>
          )}
        </p>
      </div>
      <div className='flex-none flex flex-wrap gap-2 justify-center'>
        <TypeButtonGroup type={type} setType={setType} />
        <ThemeButtonGroup theme={theme} setTheme={setTheme} />
        <FontButtonGroup font={font} setFont={setFont} />
        <AgencyButtonGroup agency={agency} setAgency={setAgency} />
      </div>
    </div>
  )
}

export default DashboardDemo

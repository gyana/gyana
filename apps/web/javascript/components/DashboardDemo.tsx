import React, { useEffect, useState } from 'react'
import ReactFC from 'react-fusioncharts'
import FusionCharts from 'fusioncharts'
import ChartLibrary from 'fusioncharts/fusioncharts.charts'
import FusionTheme from 'fusioncharts/themes/fusioncharts.theme.fusion'

ReactFC.fcRoot(FusionCharts, ChartLibrary, FusionTheme)

FusionCharts.options.license({
  key: window.FUSIONCHARTS_LICENCE,
  creditLabel: false,
})

import chartData from './dashboard-demo-data'
import { useDemoStore } from '../store'

const TYPE_CONFIG = [
  { id: 'pie2d', icon: 'fa-chart-pie' },
  { id: 'column2d', icon: 'fa-chart-bar' },
  { id: 'line', icon: 'fa-chart-line' },
  { id: 'area2d', icon: 'fa-chart-area' },
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
          className={`p-2 text-lg lg:text-xl focus:outline-none h-full ${type === option.id
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
          className={`p-2 focus:outline-none w-10 h-full ${theme === id ? `bg-${id}-600 hover:bg-${id}-700` : `bg-${id}-100 hover:bg-${id}-200`
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
          className={`p-2 text-lg lg:text-xl focus:outline-none w-10 h-full ${font === id
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
          className={`p-2 text-lg lg:text-xl focus:outline-none w-10 h-full ${agency === id
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
  const [type, setType] = useState('pie2d')
  const [theme, setTheme] = useState('indigo')
  const [font, setFont] = useState('sans-serif')
  const [agency, setAgency] = useState('squirrel')
  const [data, setData] = useState(chartData)

  const { integrations, node } = useDemoStore()[0]

  const chartConfigs = {
    type,
    width: '100%',
    height: '60%',
    dataFormat: 'json',
    dataSource: {
      chart: {
        baseFont: font,
        xAxisNameFont: font,
        yAxisNameFont: font,
        captionFont: font,
        labelFont: font,
        legendItemFont: font,
        bgColor: '#ffffff',
        theme: 'fusion',
        paletteColors: THEME_CONFIG.find((item) => item.id === theme)?.palette,
        animation: '0',
        showLegend: false,
      },
      data,
    },
  }

  useEffect(() => {
    setData(
      chartData.map(({ label, value }) => ({
        label,
        value: value + Math.floor(Math.random() * 240) - 120,
      }))
    )
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
            <span className='text-black-20'>https://</span>reports.{agency}.com
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
        <div className='p-2'>
          <ReactFC {...chartConfigs} />
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

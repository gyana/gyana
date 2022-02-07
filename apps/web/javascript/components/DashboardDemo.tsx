import React, { useState } from 'react'
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
      '#4f46e5',
      '#4338ca',
      '#3730a3',
      '#312e81',
      '#e0e7ff',
      '#c7d2fe',
      '#a5b4fc',
      '#818cf8',
      '#6366f1',
    ],
  },
  {
    id: 'green',
    palette: [
      '#38a169',
      '#2f855a',
      '#276749',
      '#22543d',
      '#f0fff4',
      '#c6f6d5',
      '#9ae6b4',
      '#68d391',
      '#48bb78',
    ],
  },
  {
    id: 'yellow',
    palette: [
      '#d69e2e',
      '#b7791f',
      '#975a16',
      '#744210',
      '#fffff0',
      '#fefcbf',
      '#faf089',
      '#f6e05e',
      '#ecc94b',
    ],
  },
]

const TypeButtonGroup = ({ type, setType }) => {
  return (
    <div className='pad flex divide-x card card--none'>
      {TYPE_CONFIG.map((option) => (
        <button
          key={option.id}
          className={`p-2 focus:outline-none ${
            type === option.id
              ? 'text-white bg-indigo-600 hover:bg-indigo-700'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          onClick={() => setType(option.id)}
        >
          <i className={`fa ${option.icon} fa-lg`}></i>
        </button>
      ))}
    </div>
  )
}

const ThemeButtonGroup = ({ theme, setTheme }) => {
  return (
    <div className='pad flex divide-x card card--none'>
      {THEME_CONFIG.map(({ id }) => (
        <button
          key={id}
          className={`p-2 focus:outline-none w-10 h-full ${
            theme === id ? `bg-${id}-600 hover:bg-${id}-700` : `bg-${id}-100 hover:bg-${id}-200`
          }`}
          onClick={() => setTheme(id)}
        ></button>
      ))}
    </div>
  )
}

const DashboardDemo = () => {
  const [type, setType] = useState('pie2d')
  const [theme, setTheme] = useState('indigo')

  const chartConfigs = {
    type,
    width: '100%',
    height: '100%',
    dataFormat: 'json',
    dataSource: {
      chart: {
        xAxisName: 'Country',
        yAxisName: 'Reserves (MMbbl)',
        theme: 'fusion',
        paletteColors: THEME_CONFIG.find((item) => item.id === theme)?.palette,
        animation: '0',
      },
      data: chartData,
    },
  }

  return (
    <div className='flex flex-col gap-4 h-full'>
      <div className='card card--none flex-grow'>
        <ReactFC {...chartConfigs} />
      </div>
      <div className='flex-none flex flex-wrap gap-2'>
        <TypeButtonGroup type={type} setType={setType} />
        <ThemeButtonGroup theme={theme} setTheme={setTheme} />
      </div>
    </div>
  )
}

export default DashboardDemo

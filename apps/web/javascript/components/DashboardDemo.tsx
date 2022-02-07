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

const ButtonGroup = ({ config, item, setItem }) => {
  return (
    <div className='pad flex divide-x card card--none'>
      {config.map((option) => (
        <button
          key={option.id}
          className={`p-2 focus:outline-none ${
            item === option.id
              ? 'text-white bg-indigo-600 hover:text-indigo-700'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          onClick={() => setItem(option.id)}
        >
          <i className={`fa ${option.icon} fa-lg`}></i>
        </button>
      ))}
    </div>
  )
}

const DashboardDemo = () => {
  const [type, setType] = useState('area2d')

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
      },
      data: chartData,
    },
  }

  return (
    <div className='flex flex-col gap-2 h-full'>
      <div className='card card--none flex-grow'>
        <ReactFC {...chartConfigs} />
      </div>
      <div className='flex-none flex flex-wrap'>
        <ButtonGroup config={TYPE_CONFIG} item={type} setItem={setType} />
      </div>
    </div>
  )
}

export default DashboardDemo

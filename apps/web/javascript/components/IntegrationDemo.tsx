import React from 'react'
import { useDemoStore } from '../state'

const SERVICES = JSON.parse(
  (document.getElementById('services') as HTMLScriptElement).textContent as string
)

const IntegrationDemo = () => {
  const [{ integrations, node }, setDemoStore] = useDemoStore()
  const integrationIds = integrations.map((s) => s.id)

  return (
    <>
      <div className='fade-left'></div>
      <div className='flex flex-col gap-4 overflow-hidden mt-2'>
        {SERVICES.map((group, idx) => (
          <div key={idx} className={`flex gap-2 integrations-${idx}`}>
            {group.services
              .filter((service) => !integrationIds.includes(service.id))
              .map((service) => (
                <button
                  key={service.id}
                  className='inline-flex items-center gap-2 flex-none px-2 py-1 rounded-lg text-sm font-normal focus:outline-none bg-indigo-100 hover:bg-indigo-200 text-gray-800'
                  onClick={() => setDemoStore({ node, integrations: [service, integrations[0]] })}
                >
                  <img
                    className='h-4 w-4'
                    src={`/static/images/integrations/fivetran/${service.icon_path}`}
                    alt={service.name}
                  />
                  {service.name}
                </button>
              ))}
          </div>
        ))}

        <div className='flex gap-2 justify-center'>
          {integrations.map((item) => (
            <div
              key={item.id}
              className='inline-flex items-center gap-2 flex-none px-2 py-1 rounded-lg text-sm font-normal focus:outline-none bg-indigo-200 border border-indigo-600 text-gray-800'
            >
              <img
                className='h-4 w-4'
                src={`/static/images/integrations/fivetran/${item.icon_path}`}
                alt={item.name}
              />
              {item.name}
            </div>
          ))}
        </div>
      </div>
      <div className='fade-right'></div>
    </>
  )
}

export default IntegrationDemo

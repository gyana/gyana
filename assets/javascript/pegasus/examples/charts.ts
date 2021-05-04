'use strict';

import {API_ROOT} from "./const";
import {getAction} from '../../api';


function renderChart(chartType, bindTo, data) {
  c3.generate({
    bindto: bindTo,
    data: {
      columns: data,
      type: chartType,
    }
  });
}


function getListEmployeesAction() {
  return getAction(API_ROOT, ["employee-data", "list"]);
}


export const Charts = {
  renderChart: renderChart,
  getListEmployeesAction: getListEmployeesAction,
};

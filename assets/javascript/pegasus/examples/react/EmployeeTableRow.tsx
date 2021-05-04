import React from "react";
import {Link} from "react-router-dom";

const EmployeeTableRow = function (props) {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  return (
    <tr>
      <td>{props.name}</td>
      <td>{props.department}</td>
      <td className="pg-text-right">{ formatter.format(props.salary) }</td>
      <td className="pg-inline-buttons pg-justify-content-end">
          <Link to={`/edit/${props.id}`}>
            <div className="pg-button-secondary">
              <span className="icon is-small"><i className="fa fa-edit" /></span>
              <span className="pg-hidden-mobile-inline">Edit</span>
            </div>
          </Link>
          <a style={{'marginLeft': '1em'}} onClick={() => props.delete(props.index)}>
            <div className="pg-button-danger">
              <span className="icon is-small"><i className="fa fa-times" /></span>
              <span className="pg-hidden-mobile-inline">Delete</span>
            </div>
          </a>
      </td>
    </tr>
  );
}

export default EmployeeTableRow;

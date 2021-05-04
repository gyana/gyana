import React, {useState, useEffect} from "react";
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link,
} from "react-router-dom";
import EditAddEmployeeWidget from "./EditAddEmployeeWidget";
import {getAction} from "../../../api";
import {API_ROOT} from "../const";
import EmployeeTableRow from "./EmployeeTableRow";


const EmptyEmployeeList = function() {
  return (
    <section className="app-card">
      <div className="pg-columns">
        <div className="pg-column-one-third">
          <img className="img-fluid" alt="Nothing Here" src={STATIC_FILES.undraw_empty}/>
        </div>
        <div className="pg-column">
          <h1 className="pg-title">No Employees Yet!</h1>
          <h2 className="pg-subtitle">Create your first employee below to get started.</h2>
          <div className="my-3">
            <Link to="/new">
              <button className="pg-button-primary">
                <span className="icon is-small"><i className="fa fa-plus"></i></span>
                <span>Create Employee</span>
              </button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
};

const EmployeeList = function(props) {
  return (
    <section className="app-card">
      <h3 className="pg-subtitle">All Employees</h3>
      <table className="table pg-table">
        <thead>
        <tr>
          <th className="pg-text-left">Name</th>
          <th className="pg-text-left">Department</th>
          <th className="pg-text-right">Salary</th>
          <th></th>
        </tr>
        </thead>
        <tbody>
        {
          props.employees.map((employee, index) => {
            // https://stackoverflow.com/a/27009534/8207
            return <EmployeeTableRow key={employee.id} index={index} {...employee}
                                     delete={(index) => props.deleteEmployee(index)}
            />;
          })
        }
        </tbody>
      </table>
      <Link to="/new">
        <button className="pg-button-primary">
          <span className="icon is-small">
            <i className="fa fa-plus"></i>
          </span>
          <span>Add Employee</span>
        </button>
      </Link>
    </section>
  );
};

const Loading = function() {
  return (
    <div className='app-card pg-text-centered'>
      <div className="lds-ripple"><div></div><div></div></div>
      <p className="heading has-text-primary">Loading...</p>
    </div>
  )
}

const EmployeeApplication = function(props) {
  const [isLoading, setIsLoading] = useState(true);
  const [employees, setEmployees] = useState([]);
  const client = props.client;

  useEffect(() => {
    const action = getAction(API_ROOT, ["employees", "list"]);
    client.action(window.schema, action).then((result) => {
      setEmployees(result.results);
      setIsLoading(false);
    });
  }, []);

  const getEmployeeById = function(id) {
    for (const employee of employees) {
      if (employee.id.toString() === id) {
        return employee;
      }
    }
  };

  const handleEmployeeSaved = function(employee) {
    let found = false;
    const newEmployees = [];
    for (let existingEmployee of employees) {
      if (existingEmployee.id === employee.id) {
        newEmployees.push(employee);
        found = true;
      } else {
        newEmployees.push(existingEmployee);
      }
    }
    if (!found) {
      newEmployees.push(employee);
    }
    setEmployees(newEmployees);
  };

  const deleteEmployee = function (index) {
    const action = getAction(API_ROOT, ["employees", "delete"]);
    const params = {id: employees[index].id};
    client.action(window.schema, action, params).then((result) => {
      const newEmployees = employees.slice(0, index).concat(employees.slice(index + 1));
      setEmployees(newEmployees);
    });
  };

  const renderEditEmployee = function (props) {
    if (isLoading) {
      return <Loading/>;
    } else {
      const employeeId = props.match.params.employeeId;
      const employee = getEmployeeById(employeeId);
      return (
        <EditAddEmployeeWidget client={client} {...employee} employeeSaved={handleEmployeeSaved}/>
      );

    }

  };

  const getDefaultView = function() {
    if (isLoading) {
      return <Loading/>
    }
    if (employees.length === 0) {
      return <EmptyEmployeeList/>;
    } else {
      return <EmployeeList employees={employees} deleteEmployee={deleteEmployee}/>
    }
  };

  return (
    <Router basename='/pegasus/objects/react/'>
      <Switch>
        <Route path="/new">
          <EditAddEmployeeWidget client={client} employeeSaved={handleEmployeeSaved}/>
        </Route>
        <Route path="/edit/:employeeId" render={(props) => renderEditEmployee(props)}>
        </Route>
        <Route path="/">
          {getDefaultView()}
        </Route>
       </Switch>
    </Router>
  );
};


export default EmployeeApplication;

import React from "react";
import {Link} from "react-router-dom";


export const TeamTableRow = function(props) {
  return (
    <tr>
      <td>{props.name}</td>
      <td><a href={props.dashboard_url}>View Dashboard</a></td>
      <td className="pg-inline-buttons pg-justify-content-end">
        <Link to={`/edit/${props.slug}`}>
          <button className="pg-button-secondary mx-1">
            <span className="icon is-small"><i className="fa fa-gear" /></span>
            <span className="pg-hidden-mobile-inline">{props.is_admin ? 'Edit' : 'View Details'}</span>
          </button>
        </Link>
        {props.is_admin ? (
          <button className="pg-button-danger mx-1" onClick={() => props.delete(props.index)}>
            <span className="icon is-small"><i className="fa fa-times" /></span>
            <span className="pg-hidden-mobile-inline">Delete</span>
          </button>
        ) : ''}
      </td>
    </tr>
  );
};


export const TeamList = function(props) {

  return (
    <section className="app-card">
      <h3 className="pg-subtitle">My Teams</h3>
      <table className="table pg-table">
        <thead>
        <tr>
          <th>Name</th>
          <th></th>
          <th></th>
        </tr>
        </thead>
        <tbody>
        {
          props.teams.map((team, index) => {
            return <TeamTableRow key={team.id} index={index} {...team}
                                 edit={(index) => props.editTeam(index)}
                                 delete={(index) => props.deleteTeam(index)}
            />;
          })
        }
        </tbody>
      </table>
      <Link to="/new">
        <button className="pg-button-secondary">
          <span className="icon is-small">
            <i className="fa fa-plus"></i>
          </span>
          <span>Add Team</span>
        </button>
      </Link>
    </section>
  );
}

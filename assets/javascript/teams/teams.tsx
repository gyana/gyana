'use strict';
import React from "react";
import ReactDOM from "react-dom";
import {TeamMemberList} from './TeamMembers'
import {InvitationList} from './Invitations'
import {getAPIAction} from "./api";


class TeamTableRow extends React.Component {
  render() {
    return (
      <tr>
        <td>{this.props.name}</td>
        <td><a href={this.props.dashboard_url}>View Dashboard</a></td>
        {/*<td>{moment(this.props.created_on).format('MMM Do YYYY, h:mm a')}</td>*/}
        <td className="pg-inline-buttons pg-justify-content-end">
          <button className="pg-button-secondary" onClick={() => this.props.edit(this.props.index)}>
            <span className="icon is-small"><i className="fa fa-edit" /></span>
            <span className="pg-hidden-mobile-inline">Edit</span>
          </button>
          <button className="pg-button-danger mx-2" onClick={() => this.props.delete(this.props.index)}>
            <span className="icon is-small"><i className="fa fa-times" /></span>
            <span className="pg-hidden-mobile-inline">Delete</span>
          </button>
        </td>
      </tr>
    );
  }
}

class EditAddTeamWidget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      name: props.team ? props.team.name : "",
      slug: props.team ? props.team.slug : "",
      editMode: Boolean(props.team),
    };
    this.nameChanged = this.nameChanged.bind(this);
    this.slugChanged = this.slugChanged.bind(this);
    this.save = this.save.bind(this);
    this.cancel = this.cancel.bind(this);
  }

  render() {
    return (
      <div>
        {this.renderDetails()}
        {this.renderMembers()}
        {this.renderInvitations()}
      </div>
    )
  }

  renderDetails() {
    return (
      <section className="app-card">
        <form>
          <h3 className="pg-subtitle">Team Details</h3>
          <div className="mb-3">
            <label className="label form-label">Team Name</label>
            <input className="input form-control" type="text" placeholder="Dunder Mifflin"
                   onChange={this.nameChanged} value={this.state.name}>
            </input>
            <p className="help form-text">Your team name.</p>
          </div>
          {this._renderIdField()}
          <div className="pg-inline-buttons">
            <button className={this.state.editMode ? 'pg-button-secondary' : 'pg-button-primary'}
                    onClick={this.save}>
                            <span className="icon is-small">
                                <i className={`fa ${this.state.editMode ? 'fa-check' : 'fa-plus'}`}></i>
                            </span>
              <span>{this.state.editMode ? 'Save Team' : 'Add Team'}</span>
            </button>
            <button className="pg-button-light mx-2" onClick={this.cancel}>
              <span>Cancel</span>
            </button>
          </div>
        </form>
      </section>
    );
  }

  _renderIdField() {
    if (this.state.editMode) {
      return (
        <div className="mb-3">
          <label className="label form-label">Team ID</label>
          <input className="input form-control" type="text" placeholder="dunder-mifflin"
                 onChange={this.slugChanged} value={this.state.slug}>
          </input>
          <p className="help form-text">A unique ID for your team. No spaces are allowed!</p>
        </div>
      );
    }
  }

  renderMembers() {
    if (this.state.editMode) {
      return (
        <TeamMemberList members={this.props.team.members}/>
      );
    } else {
      return null;
    }

  }

  renderInvitations() {
    if (this.state.editMode) {
      return (
        <InvitationList team={this.props.team} client={this.props.client}/>
      );

    } else {
      return null;
    }
  }

  nameChanged(event) {
    this.setState({name: event.target.value});
  }

  slugChanged(event) {
    this.setState({slug: event.target.value});
  }

  save(event) {
    this.props.save(this.props.team, this.state.name, this.state.slug);
    event.preventDefault();
  }

  cancel(event) {
    this.props.cancel();
    event.preventDefault();
  }

}


class TeamApplication extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      client: null,
      loading: true,
      teams: null,
      activeObject: null,
    };
    this._initializeTeams = this._initializeTeams.bind(this);
    this._cancelEdit = this._cancelEdit.bind(this);
    this._editTeam = this._editTeam.bind(this);
    this._saveTeam = this._saveTeam.bind(this);
  }

  componentDidMount() {
    this.setState({
      client: client,
    });
    let action = getAPIAction(["teams", "list"]);
    client.action(window.schema, action).then((result) => {
      this._initializeTeams(result.results);
    });
  }

  _initializeTeams(teams) {
    this.setState({
      loading: false,
      teams: teams,
    });
  }

  render() {
    if (this.state.loading) {
      return 'Loading teams...';
    } else if (this.state.editMode) {
      return (
        <EditAddTeamWidget save={this._saveTeam}
                           cancel={this._cancelEdit}
                           team={this.state.activeObject}
                           client={this.state.client}
        />

      );
    }
    if (this.state.teams.length === 0) {
      return this.renderEmpty();
    } else {
      return this.renderTeams();
    }
  }

  renderEmpty() {
    return (
      <section className="app-card">
        <div className="columns">
          <div className="column is-one-third">
            <img alt="Nothing Here" src={STATIC_FILES.undraw_team}/>
          </div>
          <div className="column is-two-thirds">
            <h1 className="title is-4">No Teams Yet!</h1>
            <h2 className="subtitle">Create your first team below to get started.</h2>

            <p>
              <a className="button is-primary" onClick={() => this._newTeam()}>
                <span className="icon is-small"><i className="fa fa-plus"></i></span>
                <span>Create Team</span>
              </a>
            </p>
          </div>
        </div>
      </section>
    );
  }

  renderTeams() {
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
            this.state.teams.map((team, index) => {
              return <TeamTableRow key={team.id} index={index} {...team}
                                   edit={(index) => this._editTeam(index)}
                                   delete={(index) => this._deleteTeam(index)}
              />;
            })
          }
          </tbody>
        </table>
        <button className="pg-button-secondary" onClick={() => this._newTeam()}>
                <span className="icon is-small">
                    <i className="fa fa-plus"></i>
                </span>
          <span>Add Team</span>
        </button>
      </section>
    )
  }

  _newTeam() {
    this.setState({
      editMode: true,
    });
  }

  _editTeam(index) {
    this.setState({
      activeObject: this.state.teams[index],
      editMode: true,
    });
  }

  _deleteTeam(index) {
    let action = getAPIAction(["teams", "delete"]);
    let params = {id: this.state.teams[index].id}
    this.state.client.action(window.schema, action, params).then((result) => {
      this.state.teams.splice(index, 1);
      this.setState({
        teams: this.state.teams
      });
    });
  }

  _saveTeam(team, name, slug) {
    let params = {
      name: name,
    };
    if (Boolean(team)) {
      params['id'] = team.id;
      params['slug'] = slug;

      let action = getAPIAction(["teams", "partial_update"]);
      this.state.client.action(window.schema, action, params).then((result) => {
        // find the appropriate item in the list and update in place
        for (var i = 0; i < this.state.teams.length; i++) {
          if (this.state.teams[i].id === result.id) {
            this.state.teams[i] = result;
          }
        }
        this.setState({
          editMode: false,
          activeObject: null,
          teams: this.state.teams,
        });
      });
    } else {
      let action = getAPIAction(["teams", "create"]);
      this.state.client.action(window.schema, action, params).then((result) => {
        this.state.teams.push(result);
        this.setState({
          editMode: false,
          activeObject: null,
          teams: this.state.teams,
        });
      });
    }
  }

  _cancelEdit(name, value) {
    this.setState({
      editMode: false,
      activeObject: null,
    });
  }

}


let auth = new coreapi.auth.SessionAuthentication({
  csrfCookieName: 'csrftoken',
  csrfHeaderName: 'X-CSRFToken'
});
let client = new coreapi.Client({auth: auth});
let domContainer = document.querySelector('#team-content');
domContainer ? ReactDOM.render(
  <TeamApplication/>
  , domContainer) : null;

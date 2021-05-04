'use strict';
import React from "react";
import ReactDOM from "react-dom";
import {Cookies} from "../app";
import {getAPIAction} from "./api";


class InviteWidget extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            email: "",
            client: props.client,
        };
        this.emailChanged = this.emailChanged.bind(this);
        this.invite = this.invite.bind(this);
    }

    render() {
        return (
            <div>
                <h3 className="pg-subtitle">Invite Team Members</h3>
                <div className="field">
                  <input className="input form-control" type="email" placeholder="michael@dundermifflin.com"
                         onChange={this.emailChanged} value={this.state.email}>
                  </input>
                  <a className="pg-button-secondary mt-2" onClick={this.invite}>
                    <span className="icon is-small">
                      <i className="fa fa-envelope-o"></i>
                    </span>
                    <span>Invite</span>
                  </a>
                </div>
            </div>
        );
    }

    emailChanged(event) {
        this.setState({email: event.target.value});
    }

    invite() {
        let action = getAPIAction(["invitations", "create"]);
        let params = {
            'team': this.props.team.id,
            'email': this.state.email,
        };
        this.state.client.action(window.schema, action, params).then((result) => {
            this.props.addInvitation(result);
            this.setState({
                email: '',
            });
        });
    }
}

class InvitationTableRow extends React.Component {
  render() {
    return (
      <tr>
        <td>{this.props.email}</td>
        <td>{this.props.role}</td>
        <td>
          <div className="pg-inline-buttons pg-justify-content-end">
            <a className="pg-button-secondary" onClick={() => this.props.resendInvitation(this.props.index)}>
              <span>{ this.props.sent ? "Sent!" : "Resend Invitation" }</span>
            </a>
            <a className="pg-button-secondary mx-2" onClick={() => this.props.delete(this.props.index)}>
              <span>Cancel Invitation</span>
            </a>
          </div>
        </td>
      </tr>
    );
  }
}


export class InvitationList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      invitations: this.props.team.invitations,
      client: props.client,
    };
    this._addInvitation = this._addInvitation.bind(this);
    this._deleteInvitation = this._deleteInvitation.bind(this);
    this._resendInvitation = this._resendInvitation.bind(this);
  }

  render() {
    return (
      <section className="app-card">
        <InviteWidget team={this.props.team} client={this.props.client} addInvitation={this._addInvitation}/>
        {this.renderPendingInvitations()}
      </section>
    );
  }

  renderPendingInvitations() {
    if (this.state.invitations.length === 0) {
      return (
        <p className="my-2 has-text-grey text-muted">
          Any pending invitations will show up here until accepted.
        </p>
      );
    }
    return (
      <div>
        <br/>
        <h3 className='pg-subtitle'>Pending Invitations</h3>
        <table className="table pg-table">
          <thead>
          <tr>
            <th>Email</th>
            <th>Role</th>
            <th></th>
          </tr>
          </thead>
          <tbody>
          {
            this.props.team.invitations.map((invitation, index) => {
              return <InvitationTableRow key={invitation.id} index={index} {...invitation}
                                         delete={(index) => this._deleteInvitation(index)}
                                         resendInvitation={(index) => this._resendInvitation(index)}
              />;
            })
          }
          </tbody>
        </table>
      </div>
    );
  }

  _addInvitation(invitation) {
    this.state.invitations.push(invitation);
    this.setState({
      invitations: this.state.invitations,
    });
  }

  _deleteInvitation(index) {
    let action = getAPIAction(["invitations", "delete"]);
    let params = {id: this.state.invitations[index].id};
    this.state.client.action(window.schema, action, params).then((result) => {
      this.state.invitations.splice(index, 1);
      this.setState({
        invitations: this.state.invitations
      });
    });
  }

  _resendInvitation(index) {
    const inviteUrl = getInviteUrl(this.props.team.slug, this.state.invitations[index].id);
    fetch(inviteUrl, {
      method: "POST",
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': Cookies.get('csrftoken'),
      }
    }).then((response) => {
      if (response.ok) {
        this.state.invitations[index].sent = true;
        this.setState({
          invitations: this.state.invitations,
        });
      }
    });
  }
}

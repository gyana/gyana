'use strict';
import React from "react";
import ReactDOM from "react-dom";


class TeamMemberTableRow extends React.Component {
    render() {
        return (
            <tr>
                <td>{this.props.display_name}</td>
                <td>{this.props.role}</td>
            </tr>
        );
    }
}

export class TeamMemberList extends React.Component {
    render() {
        return (
            <section className="app-card">
                <h3 className="pg-subtitle">Team Members</h3>
                <table className="table is-striped is-fullwidth">
                    <thead>
                    <tr>
                        <th>Member</th>
                        <th>Role</th>
                    </tr>
                    </thead>
                    <tbody>
                    {
                        this.props.members.map((membership, index) => {
                            return <TeamMemberTableRow key={membership.id} index={index} {...membership}

                            />;
                        })
                    }
                    </tbody>
                </table>

                {}
            </section>
        );
    }
}

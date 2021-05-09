'use strict';
import React, {useState, useEffect} from "react";
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link,
} from "react-router-dom";
import {getAPIAction} from "./api";
import TeamDetails from "./TeamDetails";
import {TeamList} from "./TeamList";
import LoadingScreen from "../utilities/Loading";


const NoTeams = function() {
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
            <Link to="/new">
              <a className="button is-primary">
                <span className="icon is-small"><i className="fa fa-plus"></i></span>
                <span>Create Team</span>
              </a>
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
};


const getTeamBySlug = function(teams, slug) {
  for (const team of teams) {
    if (team.slug === slug) {
      return team;
    }
  }
};


const TeamApplication = function(props) {
  const [loading, setLoading] = useState(true);
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    const action = getAPIAction(["teams", "list"]);
    props.client.action(window.schema, action).then((result) => {
      initializeTeams(result.results);
    });
  }, []);

  const initializeTeams = function (teams) {
    setTeams(teams);
    setLoading(false);
  };

  const deleteTeam = function(index) {
    let action = getAPIAction(["teams", "delete"]);
    let params = {id: teams[index].id}
    props.client.action(window.schema, action, params).then((result) => {
      teams.splice(index, 1);
      setTeams([...teams]);
    });
  };


  const saveTeam = function(team, name, slug) {
    const params = {
      name: name,
    };
    if (Boolean(team)) {
      params['id'] = team.id;
      params['slug'] = slug;

      const action = getAPIAction(["teams", "partial_update"]);
      props.client.action(window.schema, action, params).then((result) => {
        // find the appropriate item in the list and update in place
        for (let i = 0; i < teams.length; i++) {
          if (teams[i].id === result.id) {
            teams[i] = result;
          }
        }
        setTeams([...teams]);
      });
    } else {
      const action = getAPIAction(["teams", "create"]);
      props.client.action(window.schema, action, params).then((result) => {
        teams.push(result);
        setTeams([...teams]);
      });
    }
  };

  const getDefaultView = function() {
    if (loading) {
      return <LoadingScreen/>
    }
    if (teams.length === 0) {
      return <NoTeams/>;
    } else {
      return <TeamList teams={teams}
                       deleteTeam={deleteTeam} />;

    }
  };

  const renderEditTeam = function(routerProps) {
    if (loading) {
      return <LoadingScreen />;
    } else {
      const team = getTeamBySlug(teams, routerProps.match.params.teamSlug);
      return (
        <TeamDetails save={saveTeam}
                     returnUrl='/'
                     team={team}
                     client={props.client}
                     apiUrls={props.apiUrls}
        />
      );
    }
  };

  return (
    <Router basename={props.urlBase}>
      <Switch>
        <Route path="/new">
          <TeamDetails save={saveTeam}
                       returnUrl='/'
                       team={null}
                       client={props.client}
                       apiUrls={props.apiUrls}
          />
        </Route>
        <Route path="/edit/:teamSlug" render={(props) => renderEditTeam(props)}>
        </Route>
        <Route path="/">
          {getDefaultView()}
        </Route>
       </Switch>
    </Router>
  );
};

export default TeamApplication;

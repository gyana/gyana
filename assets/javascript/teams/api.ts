import {getAction} from "../api";

const API_PREFIX = ['teams', 'api'];

export function getAPIAction(action) {
    return getAction(API_PREFIX, action);
}


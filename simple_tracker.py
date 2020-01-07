import numpy as np
from cv2 import KalmanFilter
from sortedcontainers import SortedDict

M = 3
N = 4
RETIRE_COUNT = 3
ASSOCIATION_RADIUS = 1


class Track:
    def __init__(self, position, velocity):
        self.kf = KalmanFilter(2, 1, 0)
        self.kf.statePost = np.array([[position], [velocity]])
        self.kf.errorCovPost = 1. * np.ones((2, 2))
        self.kf.transitionMatrix = np.array([[1., 1.], [0., 1.]])
        self.kf.measurementMatrix = 1. * np.ones((1, 2))
        self.kf.measurementMatrix[0, 1] = 0.
        self.kf.processNoiseCov = 1e-5 * np.eye(2)
        self.kf.measurementNoiseCov = 1e-3 * np.ones((1, 1))
        # self.position = position
        # self.velocity = velocity
        # self.old_position = None
        self.m = 1
        self.n = 1

    def position_pre(self):
        return self.kf.statePre[0, 0]

    def velocity_pre(self):
        return self.kf.statePre[1, 0]

    def position_post(self):
        return self.kf.statePost[0]

    def velocity_post(self):
        return self.kf.statePost[1]


def update_track(track, obs_position):
    track.kf.correct(np.array([obs_position]))
    track.m = min(M, track.m + 1) if track.n <= N else M


def propagate_track(track, delta_t):
    track.kf.transitionMatrix[0, 1] = delta_t
    track.kf.predict()
    track.n += 1
    track.m = track.m - 1 if track.n > N else track.m


class SimpleTracker:
    def __init__(self, initial_velocity):
        self.initial_velocity = initial_velocity
        self.active_tracks = {}
        self.retired_tracks = {}
        self.track_count = -1

    def start_track(self, position, direction):
        self.track_count += 1
        self.active_tracks[self.track_count] = Track(position, self.initial_velocity*direction)

    def update_tracks(self, observations, directions, delta_t):
        # Propagate tracks
        [propagate_track(v, delta_t) for v in self.active_tracks.values()]
        assignments = {}
        taken_tracks = set()

        # Associate tracks
        print(observations)
        sorted_distances = SortedDict()
        for obs in range(len(observations)):
            for track, v in self.active_tracks.items():
                distance = abs(observations[obs] - v.position_pre())
                if distance < ASSOCIATION_RADIUS:
                    sorted_distances.update({distance: (obs, track)})

        for k, v in sorted_distances.items():
            if v[0] not in assignments and v[1] not in taken_tracks:
                assignments[v[0]] = v[1]
                taken_tracks.add(v[1])

        print(assignments)
        # Update tracks that are associated, and create new ones.
        for i in range(len(observations)):
            if i in assignments:
                update_track(self.active_tracks[assignments[i]], observations[i])
            else:
                self.start_track(observations[i], directions[i])

        # Retire old tracks and delete other ones.
        to_delete = []
        to_retire = []
        for k, track in self.active_tracks.items():
            if track.n is N and track.m < M:
                to_delete.append(k)
            elif track.n > N and track.m is 0:
                to_retire.append(k)

        for t in to_retire:
            self.retired_tracks[t] = self.active_tracks[t]

        for t in to_retire + to_delete:
            del self.active_tracks[t]

    def get_active_tracks(self):
        return self.active_tracks

    def get_retired_tracks(self):
        return self.retired_tracks

    def print_tracks(self):
        if self.active_tracks:
            print("Track, Position, Velocity")
            [print(k, v.position_post(), v.velocity_post()) for k, v in self.active_tracks.items()]

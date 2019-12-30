
M = 3
N = 4
RETIRE_COUNT = 3
ASSOCIATION_RADIUS = 1

class Track:
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity
        self.m = 1
        self.n = 1


def update_track(track, obs_position, delta_t):
    old_position = track.position
    track.position = (track.position + obs_position) / 2.0
    track.velocity = (track.position - old_position) / delta_t
    track.m = min(M, track.m + 1) if track.n <= N else M


def propagate_track(track, delta_t):
    track.position = track.position + track.velocity * delta_t
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

        # Associate tracks
        print(observations)
        #### CHANGE THIS FUNCTION: NEED TO START FROM CLOSEST POINT NOT GREEDY PER OBSERVATION
        for i in range(len(observations)):
            distances = {k: abs(observations[i] - v.position) for k, v in self.active_tracks.items()
                         if abs(observations[i] - v.position) < ASSOCIATION_RADIUS}
            sorted_distances = {k: v for k, v in sorted(distances.items(), key=lambda item: item[1])}
            print(sorted_distances)
            for track_key in sorted_distances.keys():
                if track_key not in assignments.values():
                    assignments[i] = track_key
                    break

        print(assignments)
        # Update tracks that are associated, and create new ones.
        for i in range(len(observations)):
            if i in assignments:
                update_track(self.active_tracks[assignments[i]], observations[i], delta_t)
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
            [print(k, v.position, v.velocity) for k, v in self.active_tracks.items()]

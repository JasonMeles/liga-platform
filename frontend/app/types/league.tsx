export type SportType = "football" | "basketball";

export type League = {
    id: number;
    name: string;
    manager_username: string;
    is_active: boolean;
    total_journeys: number;
    sport_type: SportType;
    allow_same_owner_matches: boolean;
};

export type LeagueDetail = {
    id: number;
    name: string;
    sport_type: "football" | "basketball";
    is_active: boolean;
    max_teams: number;
    max_per_player: number;
    total_journeys: number;
    manager_username: string;
    my_role: "manager" | "membre";
};

export type Team = {
    id: number;
    nom: string;
    nom_stade: string;
    owner_username: string;   // "AI" pour une équipe IA
    journeys_remaining: number;
};

export type Match = {
  id: number;
  team_home: string;
  team_away: string;
  score_home: number | null;   // null tant que le match n'est pas joué
  score_away: number | null;
  state: "PENDING" | "IN_PROGRESS" | "FINISHED";
  scheduled_at: string | null;
  stadium: string;
  round_number: number;
};
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
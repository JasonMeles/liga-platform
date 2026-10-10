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
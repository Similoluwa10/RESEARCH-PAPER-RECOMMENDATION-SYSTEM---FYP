'use client';

import { Mail, MapPin, Briefcase } from 'lucide-react';

interface ProfileCardProps {
  name: string;
  email?: string;
  affiliation?: string;
  bio?: string;
  avatar?: string;
  joinDate?: string;
  savedPapers?: number;
  recommendations?: number;
}

export default function ProfileCard({
  name,
  email,
  affiliation,
  bio,
  avatar,
  joinDate,
  savedPapers = 0,
  recommendations = 0,
}: ProfileCardProps) {
  return (
    <div className="card-base">
      {/* Avatar */}
      {avatar ? (
        <img
          src={avatar}
          alt={name}
          className="w-24 h-24 rounded-lg mb-4 object-cover"
        />
      ) : (
        <div className="w-24 h-24 rounded-lg mb-4 bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
          <span className="text-3xl font-bold text-primary-foreground">
            {name.charAt(0)}
          </span>
        </div>
      )}

      {/* Name */}
      <h2 className="text-2xl font-bold text-foreground mb-1">{name}</h2>

      {/* Bio */}
      {bio && <p className="text-muted-foreground mb-4">{bio}</p>}

      {/* Details */}
      <div className="space-y-2 mb-6 pb-6 border-b border-border">
        {email && (
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <Mail className="w-4 h-4" />
            <a href={`mailto:${email}`} className="hover:text-primary transition-colors">
              {email}
            </a>
          </div>
        )}
        {affiliation && (
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <Briefcase className="w-4 h-4" />
            <span>{affiliation}</span>
          </div>
        )}
        {joinDate && (
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span>Joined {joinDate}</span>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-2xl font-bold text-primary">{savedPapers}</p>
          <p className="text-sm text-muted-foreground">Saved Papers</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-primary">{recommendations}</p>
          <p className="text-sm text-muted-foreground">Recommendations</p>
        </div>
      </div>
    </div>
  );
}

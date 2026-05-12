import PublicWorkspace from './PublicWorkspace'

export default function RoleWorkspace({ employmentData = [], publicSalaryRankingData = [], dataLoadedAt = '' }) {
  return (
    <PublicWorkspace
      employmentData={employmentData}
      publicSalaryRankingData={publicSalaryRankingData}
      dataLoadedAt={dataLoadedAt}
    />
  )
}
